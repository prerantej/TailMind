# backend/src/services/llm_service.py
import os
import json
import re
import logging
from typing import Optional, Any, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
#  GOOGLE GENAI (new SDK) – with safe fallback detection
# ---------------------------------------------------------
GENAI_IMPL = None
genai_mod = None

try:
    from google import genai as genai_mod
    GENAI_IMPL = "google-genai"
    logger.info("Using google-genai SDK")
except Exception:
    try:
        import google.generativeai as genai_mod
        GENAI_IMPL = "google-generativeai"
        logger.info("Using legacy google-generativeai SDK")
    except Exception:
        genai_mod = None
        GENAI_IMPL = None
        logger.warning("⚠️ No Google GenAI SDK available – using dummy LLM.")

# ---------------------------------------------------------
#  IMPORT DB + MODELS (unchanged)
# ---------------------------------------------------------
from ..db import engine, create_db_and_tables, get_session
from ..models import Email, EmailProcessing, Prompt, Draft

# ---------------------------------------------------------
# LOAD ENV VARS
# ---------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---------------------------------------------------------
# Helper: attempt to create a genai client (returns None on failure)
# ---------------------------------------------------------
def _create_genai_client():
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not provided — LLM disabled.")
        return None

    if genai_mod is None:
        logger.warning("No genai SDK installed.")
        return None

    try:
        if GENAI_IMPL == "google-genai":
            # new SDK: create client instance
            # defensive: in most versions it's genai.Client(api_key=...)
            client = genai_mod.Client(api_key=GEMINI_API_KEY)
            logger.info("Created google-genai Client.")
            return client
        elif GENAI_IMPL == "google-generativeai":
            # legacy SDK
            genai_mod.configure(api_key=GEMINI_API_KEY)
            client = genai_mod.GenerativeModel(model_name=GEMINI_MODEL)
            logger.info("Created legacy google.generativeai client.")
            return client
    except Exception:
        logger.exception("Failed to initialize GenAI client.")
        return None

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
# LLM Service
# =========================================================
class LLMService:
    def __init__(self, model: str = GEMINI_MODEL):
        self.model = model
        # Create a client instance for this service (may be None)
        self.client = _create_genai_client()

    # ------------------------------
    # INTERNAL CALL WRAPPER (defensive across SDK versions)
    # ------------------------------
    def _call(self, prompt: str) -> Optional[str]:
        if not self.client or not GEMINI_API_KEY:
            logger.warning("⚠️ LLM not available – using fallback text.")
            return None

        try:
            # 1) Try new SDK shape: client.models.generate(...) => response with `.text` or structured outputs
            try:
                if hasattr(self.client, "models"):
                    # many google-genai examples use client.models.generate(...)
                    response = self.client.models.generate(model=self.model, prompt=prompt)
                    text = _extract_text_from_response(response)
                    if text is not None:
                        return text
            except Exception:
                logger.debug("client.models.generate pattern failed, trying other patterns.", exc_info=False)

            # 2) Try new SDK alternative: client.generate_text(...)
            try:
                if hasattr(self.client, "generate_text"):
                    response = self.client.generate_text(model=self.model, input=prompt)
                    text = _extract_text_from_response(response)
                    if text is not None:
                        return text
            except Exception:
                logger.debug("client.generate_text pattern failed.", exc_info=False)

            # 3) Try generic 'responses' pattern
            try:
                if hasattr(self.client, "responses") and hasattr(self.client.responses, "generate"):
                    response = self.client.responses.generate(model=self.model, input=prompt)
                    text = _extract_text_from_response(response)
                    if text is not None:
                        return text
            except Exception:
                logger.debug("client.responses.generate pattern failed.", exc_info=False)

            # 4) Legacy SDK pattern
            try:
                if GENAI_IMPL == "google-generativeai" and hasattr(self.client, "generate_content"):
                    response = self.client.generate_content(prompt)
                    return getattr(response, "text", str(response))
            except Exception:
                logger.debug("legacy client.generate_content pattern failed.", exc_info=False)

            logger.error("All GenAI call patterns failed.")
            return None

        except Exception as e:
            logger.exception("Gemini call failed: %s", e)
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
            return {"subject": parsed.get("subject", ""), "body": parsed.get("body", "")}
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
# Module-level helper to close/cleanup the client on shutdown
# ---------------------------------------------------------
async def _maybe_aclose_client():
    """
    Called by FastAPI shutdown event. Attempts to find and close the live client.
    Safe no-op if no client or no 'aclose'/'close' method.
    """
    try:
        # If global instance exists, use it
        global llm_service  # may be defined later below
        client = None
        try:
            client = getattr(llm_service, "client", None)
        except Exception:
            client = None

        if client is None:
            return

        # Prefer async aclose, else sync close if available
        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            await aclose()
            logger.info("Called client.aclose()")
            return

        close = getattr(client, "close", None)
        if callable(close):
            try:
                close()
                logger.info("Called client.close()")
                return
            except Exception:
                logger.exception("Error calling client.close() (ignored).")
    except Exception:
        logger.exception("Error closing GenAI client (ignored).")

# ---------------------------------------------------------
# Utility: try to extract plain text from several response shapes
# ---------------------------------------------------------
def _extract_text_from_response(response) -> Optional[str]:
    if response is None:
        return None

    # common patterns: response.text, response.output_text, response.output[0].text, response.candidates
    try:
        # direct attribute 'text'
        text = getattr(response, "text", None)
        if text:
            return text if isinstance(text, str) else str(text)

        # some wrappers: response.output_text
        if hasattr(response, "output_text"):
            t = getattr(response, "output_text")
            if t:
                return t if isinstance(t, str) else str(t)

        # nested: response.output[0].content / response.output[0].text
        out = getattr(response, "output", None)
        if out:
            # if list-like
            try:
                first = out[0]
                # content -> text
                t = getattr(first, "content", None) or getattr(first, "text", None)
                if t:
                    return t if isinstance(t, str) else str(t)
            except Exception:
                pass

        # some responses expose .candidates list with .text
        candidates = getattr(response, "candidates", None)
        if candidates and len(candidates) > 0:
            cand0 = candidates[0]
            t = getattr(cand0, "text", None) or getattr(cand0, "content", None)
            if t:
                return t if isinstance(t, str) else str(t)

        # fallback: str(response) but be cautious
        return str(response)
    except Exception:
        logger.exception("Failed to extract text from response object.")
        return None

# ---------------------------------------------------------
# GLOBAL INSTANCE (safe to import)
# ---------------------------------------------------------
llm_service = LLMService()
