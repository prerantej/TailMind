# backend/src/services/llm_service.py

import os
import json
import re
import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
#  GOOGLE GENAI (new SDK) – with safe fallback
# ---------------------------------------------------------

GENAI_IMPL = None
genai_mod = None

try:
    # Try the new unified SDK (recommended)
    from google import genai as genai_mod
    GENAI_IMPL = "google-genai"
    logger.info("Using google-genai SDK")
except Exception:
    try:
        # Fallback to old SDK if installed
        import google.generativeai as genai_mod
        GENAI_IMPL = "google-generativeai"
        logger.info("Using legacy google-generativeai SDK")
    except Exception:
        genai_mod = None
        GENAI_IMPL = None
        logger.warning("⚠️ No Google GenAI SDK available – using dummy LLM.")

# ---------------------------------------------------------
#  IMPORT DB + MODELS
# ---------------------------------------------------------
from ..db import engine, create_db_and_tables, get_session
from ..models import Email, EmailProcessing, Prompt, Draft

# ---------------------------------------------------------
# LOAD ENV VARS
# ---------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ---------------------------------------------------------
# Initialize GenAI client (if SDK available)
# ---------------------------------------------------------

client = None

if GENAI_IMPL == "google-genai":
    try:
        client = genai_mod.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.exception("Failed to initialize google-genai Client.")
        client = None

elif GENAI_IMPL == "google-generativeai":
    try:
        genai_mod.configure(api_key=GEMINI_API_KEY)
        client = genai_mod.GenerativeModel(model_name=GEMINI_MODEL)
    except Exception:
        logger.exception("Failed to initialize legacy google-generativeai.")
        client = None

else:
    logger.warning("No LLM SDK detected – dummy mode enabled.")


# =========================================================
#  SAFE JSON PARSER
# =========================================================
def safe_json_extract(text: str) -> Any:
    if not text:
        return None

    t = re.sub(r"```(?:json)?\n", "", text, flags=re.IGNORECASE)
    t = re.sub(r"\n```", "", t)
    t = t.strip().strip("`").strip()

    try:
        return json.loads(t)
    except Exception:
        pass

    obj_idx = t.find("{")
    arr_idx = t.find("[")
    start_idx = None
    if arr_idx != -1 and (obj_idx == -1 or arr_idx < obj_idx):
        start_idx = arr_idx
    elif obj_idx != -1:
        start_idx = obj_idx

    if start_idx is not None:
        candidate = t[start_idx:]
        try:
            return json.loads(candidate)
        except Exception:
            last_obj = candidate.rfind("}")
            last_arr = candidate.rfind("]")
            if last_obj != -1:
                try:
                    return json.loads(candidate[: last_obj + 1])
                except Exception:
                    pass
            if last_arr != -1:
                try:
                    return json.loads(candidate[: last_arr + 1])
                except Exception:
                    pass

    return None


# =========================================================
# Helper: load prompts from DB
# =========================================================
def _get_prompt_from_db(key: str) -> Optional[str]:
    try:
        with get_session() as session:
            p = session.get(Prompt, key)
            return p.text if p else None
    except Exception:
        logger.exception("Failed to load prompt from DB for key=%s", key)
        return None


# =========================================================
#  LLM SERVICE
# =========================================================
class LLMService:
    def __init__(self, model: str = GEMINI_MODEL):
        self.model = model
        self.client = client   # new or old or dummy

    # ------------------------------
    #   INTERNAL CALL WRAPPER
    # ------------------------------
    def _call(self, prompt: str) -> Optional[str]:

        if not self.client or not GEMINI_API_KEY:
            logger.warning("⚠️ LLM not available – using fallback text.")
            return None

        try:
            if GENAI_IMPL == "google-genai":
                response = self.client.models.generate(
                    model=self.model,
                    prompt=prompt
                )
                return response.text

            elif GENAI_IMPL == "google-generativeai":
                response = self.client.generate_content(prompt)
                return getattr(response, "text", str(response))

        except Exception as e:
            logger.exception("Gemini call failed: %s", e)
            return None

        return None

    # ------------------------------
    # Categorization
    # ------------------------------
    def categorize(self, email_text: str, prompt: Optional[str] = None) -> str:

        if prompt is None:
            db_prompt = _get_prompt_from_db("categorization")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                final_prompt = (
                    "Reply with ONE LABEL ONLY.\n"
                    "Valid labels: Important, Newsletter, Spam, To-Do.\n\n"
                    f"Email:\n{email_text}"
                )
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)

        if not resp:
            return self._heuristic_categorize(email_text)

        label = resp.strip().splitlines()[0].strip().split()[0]
        return label

    def _heuristic_categorize(self, text: str) -> str:
        t = text.lower()
        if "newsletter" in t or "unsubscribe" in t:
            return "Newsletter"
        if "meeting" in t or "scheduled" in t:
            return "Important"
        if "buy now" in t or "free" in t:
            return "Spam"
        return "To-Do"

    # ------------------------------
    # Task Extraction
    # ------------------------------
    def extract_tasks(self, email_text: str, prompt: Optional[str] = None):

        if prompt is None:
            db_prompt = _get_prompt_from_db("action_extraction")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                final_prompt = (
                    "Extract tasks from the email.\n"
                    "Return STRICT JSON array.\n\n"
                    f"Email:\n{email_text}"
                )
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)
        if not resp:
            return []

        parsed = safe_json_extract(resp)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]

        return resp

    # ------------------------------
    # Draft Reply
    # ------------------------------
    def generate_reply(self, email_text: str, prompt: Optional[str] = None, tone: str = "polite"):

        if prompt is None:
            db_prompt = _get_prompt_from_db("auto_reply")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                final_prompt = (
                    f"Write a {tone} reply. Return JSON: {{'subject':'', 'body':''}}.\n\n"
                    f"Email:\n{email_text}"
                )
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)
        if not resp:
            return {"subject": "", "body": "Thanks — will follow up soon."}

        parsed = safe_json_extract(resp)
        if isinstance(parsed, dict):
            return {
                "subject": parsed.get("subject", ""),
                "body": parsed.get("body", "")
            }

        return {"subject": "", "body": resp.strip()}

    # ------------------------------
    # Chat with Email Context
    # ------------------------------
    def chat_with_email(self, email_text: str, user_query: str, prompt: Optional[str] = None):

        if prompt is None:
            final_prompt = (
                "You are an intelligent assistant.\n"
                "Use ONLY the email content to answer.\n\n"
                f"Email:\n{email_text}\n\nUser:\n{user_query}"
            )
        else:
            final_prompt = prompt + "\n" + email_text + "\n\nUser:\n" + user_query

        resp = self._call(final_prompt)
        if not resp:
            return "LLM unavailable — here is a summary: " + (email_text[:350] + "...")

        return resp.strip()


# ---------------------------------------------------------
#  GLOBAL INSTANCE
# ---------------------------------------------------------
llm_service = LLMService()
