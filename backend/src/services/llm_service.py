# backend/src/services/llm_service.py
import os
import json
import re
import logging
from typing import Optional, Any, Dict, List, Union

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Relative imports to models / db in parent package (src)
from ..db import engine, create_db_and_tables, get_session
from ..models import Email, EmailProcessing, Prompt, Draft

# Load GEMINI key from environment; do not raise at import time (warn instead)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set. LLM calls will likely fail until the key is provided.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        logger.exception("Failed to configure genai client. Please verify your Gemini SDK & key.")

def safe_json_extract(text: str) -> Any:
    
    """
    Try to extract and parse JSON from `text`.
    - Strips Markdown code fences (```json ... ``` and ``` ... ```)
    - Tries direct json.loads on the stripped text
    - If that fails, finds the first '{' or '[' and attempts to parse from that index
    Returns parsed JSON object (dict/list) or None.
    """
    if not text:
        return None

    # Remove common code fences like ```json ... ``` or ``` ... ```
    t = re.sub(r"```(?:json)?\n", "", text, flags=re.IGNORECASE)
    t = re.sub(r"\n```", "", t)
    # Strip triple/back ticks and surrounding whitespace
    t = t.strip().strip("`").strip()

    # Try direct parse first
    try:
        return json.loads(t)
    except Exception:
        pass

    # Look for first JSON-like substring
    obj_idx = t.find("{")
    arr_idx = t.find("[")
    start_idx = None
    if arr_idx != -1 and (obj_idx == -1 or arr_idx < obj_idx):
        start_idx = arr_idx
    elif obj_idx != -1:
        start_idx = obj_idx

    if start_idx is not None:
        candidate = t[start_idx:]
        # Try parse candidate directly
        try:
            return json.loads(candidate)
        except Exception:
            # Try to trim to last matching bracket and parse
            last_obj = candidate.rfind("}")
            last_arr = candidate.rfind("]")
            # prefer last_obj if JSON object
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

# --- helper to fetch stored prompts from DB ---
def _get_prompt_from_db(key: str) -> Optional[str]:
    try:
        with get_session() as session:
            p = session.get(Prompt, key)
            return p.text if p else None
    except Exception:
        logger.exception("Failed to load prompt from DB for key=%s", key)
        return None

class LLMService:
    def __init__(self, model: str = GEMINI_MODEL):
        self.model = model
        # instantiate client lazily when used
        try:
            self.client = genai.GenerativeModel(model_name=self.model) if GEMINI_API_KEY else None
        except Exception:
            logger.exception("Failed to create Gemini model client.")
            self.client = None

    def _call(self, prompt: str) -> Optional[str]:
        if not GEMINI_API_KEY or not self.client:
            logger.warning("Skipping LLM call because GEMINI_API_KEY or client not configured.")
            return None
        try:
            # SDK may vary by version; this pattern matches the common usage in your code
            response = self.client.generate_content(prompt)
            # response.text is used in your prior code
            text = getattr(response, "text", None)
            if text is None:
                # try to stringify object fallback
                text = str(response)
            return text
        except Exception as e:
            logger.exception("Gemini call failed: %s", e)
            return None

    # ----------------------------
    # Categorization
    # ----------------------------
    def categorize(self, email_text: str, prompt: Optional[str] = None) -> str:
        """
        Use DB-stored prompt 'categorization' if prompt is None, else use provided prompt.
        """
        if prompt is None:
            db_prompt = _get_prompt_from_db("categorization")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                base = """
Reply with ONE LABEL ONLY.
Valid labels: Important, Newsletter, Spam, To-Do.
Email:
"""
                final_prompt = base + "\n" + email_text
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)
        if not resp:
            return self._heuristic_categorize(email_text)

        # Response may include explanation; extract first token/word if possible
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

    # ----------------------------
    # Task Extraction
    # ----------------------------
    def extract_tasks(self, email_text: str, prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ask the LLM to extract tasks. If prompt is None, load 'action_extraction' prompt from DB.
        Return a parsed list when possible, otherwise return a string or empty list.
        """
        if prompt is None:
            db_prompt = _get_prompt_from_db("action_extraction")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                base = """
Extract tasks from the email.
Return STRICT JSON array:
[
  {"task": "...", "deadline": "...", "assignee": "..."}
]
Email:
"""
                final_prompt = base + "\n" + email_text
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)

        if not resp:
            return []

        # Try to parse safely
        parsed = safe_json_extract(resp)
        if isinstance(parsed, list):
            return parsed
        # if parsed is dict or other, normalize to list
        if isinstance(parsed, dict):
            return [parsed]

        # if parsing failed, return raw string (caller will handle)
        return resp

    # ----------------------------
    # Draft Reply
    # ----------------------------
    def generate_reply(self, email_text: str, prompt: Optional[str] = None, tone: str = "polite"):
        """
        Generate a reply draft for the given email text.

        Returns a dict: {"subject": "<subject>", "body": "<body>"}.
        Behavior:
        - If a DB prompt 'auto_reply' exists and prompt is None, it will be used.
        - If the LLM returns JSON (possibly wrapped in code fences), we try to parse it
        and use subject/body keys.
        - If the LLM returns plain text, we return it as the 'body' and leave subject empty;
        caller can default to "Re: <orig subject>".
        """
        # Compose prompt (use DB stored prompt if present)
        if prompt is None:
            try:
                db_prompt = _get_prompt_from_db("auto_reply")
            except Exception:
                db_prompt = None
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                base = f"""
    Write a {tone} email reply.
    Return JSON:
    {{"subject":"...", "body":"..."}}

    Email:
    """
                final_prompt = base + "\n" + email_text
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)
        if not resp:
            # fallback
            return {"subject": "", "body": "Thanks — will follow up soon."}

        # Try to parse JSON (handles fenced codeblocks)
        parsed = None
        try:
            parsed = safe_json_extract(resp)
        except Exception:
            parsed = None

        if isinstance(parsed, dict):
            subj = parsed.get("subject") or ""
            body = parsed.get("body") or ""
            return {"subject": subj, "body": body}
        else:
            # Not JSON — return raw text as body
            text_body = resp.strip()
            return {"subject": "", "body": text_body}


    # ----------------------------
    # Chat With Email Context
    # ----------------------------
    def chat_with_email(self, email_text: str, user_query: str, prompt: Optional[str] = None):
        if prompt is None:
            base = """
You are an intelligent email assistant.
Use ONLY the email content to answer the user's question.

Email:
"""
            final_prompt = base + "\n" + email_text + "\n\nUser question:\n" + user_query
        else:
            final_prompt = prompt + "\n" + email_text + "\n\nUser question:\n" + user_query

        resp = self._call(final_prompt)
        if not resp:
            return "LLM unavailable — here is a short summary: " + (email_text[:350] + "...")

        return resp.strip()


# global instance used by other modules
llm_service = LLMService()
