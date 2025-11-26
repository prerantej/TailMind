# backend/src/services/llm_service.py
import os
import json
import re
import logging
from typing import Optional, Any, List

# Load environment variables FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# Log configuration status
if GEMINI_API_KEY:
    logger.info(f"✅ GEMINI_API_KEY loaded, using model: {GEMINI_MODEL}")
else:
    logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")

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
            client = genai_mod.Client(api_key=GEMINI_API_KEY)
            logger.info("✅ Created google-genai Client successfully.")
            return client
        elif GENAI_IMPL == "google-generativeai":
            # legacy SDK
            genai_mod.configure(api_key=GEMINI_API_KEY)
            client = genai_mod.GenerativeModel(model_name=GEMINI_MODEL)
            logger.info("✅ Created legacy google.generativeai client successfully.")
            return client
    except Exception as e:
        logger.exception(f"❌ Failed to initialize GenAI client: {e}")
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
        
        if self.client:
            logger.info(f"✅ LLMService initialized with model: {self.model}")
        else:
            logger.warning("⚠️ LLMService initialized without client - LLM features disabled")

    # ------------------------------
    # INTERNAL CALL WRAPPER (defensive across SDK versions)
    # ------------------------------
    def _call(self, prompt: str) -> Optional[str]:
        if not self.client or not GEMINI_API_KEY:
            logger.warning("⚠️ LLM not available – using fallback text.")
            return None

        try:
            # 1) Try new SDK shape: client.models.generate_content(...)
            if GENAI_IMPL == "google-genai":
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt
                    )
                    text = _extract_text_from_response(response)
                    if text:
                        logger.debug(f"✅ LLM response (first 100 chars): {text[:100]}")
                        return text
                except Exception as e:
                    logger.debug(f"client.models.generate_content failed: {e}")

            # 2) Try legacy SDK pattern
            if GENAI_IMPL == "google-generativeai" and hasattr(self.client, "generate_content"):
                try:
                    response = self.client.generate_content(prompt)
                    text = getattr(response, "text", str(response))
                    logger.debug(f"✅ LLM response (first 100 chars): {text[:100]}")
                    return text
                except Exception as e:
                    logger.debug(f"legacy generate_content failed: {e}")

            logger.error("All GenAI call patterns failed.")
            return None

        except Exception as e:
            logger.exception(f"Gemini call failed: {e}")
            return None

    # ------------------------------
    # Categorization - IMPROVED
    # ------------------------------
    def categorize(self, email_text: str, prompt: Optional[str] = None) -> str:
        if prompt is None:
            db_prompt = _get_prompt_from_db("categorization")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                # IMPROVED DEFAULT PROMPT
                final_prompt = f"""You are an expert email classifier. Analyze this email and categorize it into EXACTLY ONE of these categories:

1. **Important** - Urgent work matters, meeting requests, deadlines, boss emails, client requests, time-sensitive action items
2. **Newsletter** - Marketing emails, subscriptions, updates, digests, promotional content, automated notifications with "unsubscribe" links
3. **Spam** - Unwanted promotions, suspicious offers, scams, "buy now" messages, too-good-to-be-true deals
4. **To-Do** - Regular work tasks, follow-ups, non-urgent requests, information requests, routine work items

IMPORTANT RULES:
- Respond with ONLY ONE WORD: Important, Newsletter, Spam, or To-Do
- No explanations, no extra text, just the category name
- If an email has "unsubscribe" or is from a newsletter service, it's Newsletter
- If an email is from a boss or mentions deadlines/urgency, it's Important
- If an email has promotional language like "buy now" or "limited time", check if it's legitimate (Important/To-Do) or spam

EMAIL TO CATEGORIZE:
{email_text}

CATEGORY:"""
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)
        if not resp:
            return self._heuristic_categorize(email_text)

        # Extract and normalize category
        category = resp.strip().splitlines()[0].strip().split()[0]
        category_lower = category.lower()
        
        if "important" in category_lower:
            return "Important"
        elif "newsletter" in category_lower:
            return "Newsletter"
        elif "spam" in category_lower:
            return "Spam"
        elif "to-do" in category_lower or "todo" in category_lower:
            return "To-Do"
        else:
            logger.warning(f"⚠️ Unknown category '{category}', using heuristic")
            return self._heuristic_categorize(email_text)

    def _heuristic_categorize(self, text: str) -> str:
        """IMPROVED heuristic categorization"""
        t = text.lower()
        
        # Newsletter indicators (check first - most specific)
        if any(word in t for word in ["unsubscribe", "newsletter", "digest", "weekly", "subscription", "mailing list"]):
            logger.info("📧 Heuristic: Newsletter (unsubscribe/newsletter keywords)")
            return "Newsletter"
        
        # Important indicators
        if any(word in t for word in ["urgent", "asap", "deadline", "meeting", "scheduled", "boss", "client", "important"]):
            logger.info("📧 Heuristic: Important (urgency keywords)")
            return "Important"
        
        # Spam indicators
        if any(word in t for word in ["buy now", "limited time", "free", "winner", "claim", "click here now"]):
            logger.info("📧 Heuristic: Spam (promotional keywords)")
            return "Spam"
        
        # Default to To-Do
        logger.info("📧 Heuristic: To-Do (default)")
        return "To-Do"

    # ------------------------------
    # Task Extraction - IMPROVED
    # ------------------------------
    def extract_tasks(self, email_text: str, prompt: Optional[str] = None):
        if prompt is None:
            db_prompt = _get_prompt_from_db("action_extraction")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                # IMPROVED DEFAULT PROMPT
                final_prompt = f"""You are a task extraction assistant. Analyze this email and extract ALL actionable tasks or to-dos.

RULES:
- Return a JSON array of tasks
- Each task should have: "task" (description), "deadline" (date if mentioned, else null)
- Be specific and clear in task descriptions
- If NO tasks are found, return an empty array: []

EMAIL:
{email_text}

TASKS (JSON array):"""
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
        return []

    # ------------------------------
    # Draft Reply - IMPROVED
    # ------------------------------
    def generate_reply(self, email_text: str, prompt: Optional[str] = None, tone: str = "polite"):
        if prompt is None:
            db_prompt = _get_prompt_from_db("auto_reply")
            if db_prompt:
                final_prompt = db_prompt + "\n\nEMAIL:\n" + email_text
            else:
                # IMPROVED DEFAULT PROMPT
                final_prompt = f"""You are a professional email assistant. Write a {tone} reply to this email.

Return ONLY a JSON object with this exact format:
{{
  "subject": "Re: [original subject]",
  "body": "your reply here"
}}

EMAIL TO REPLY TO:
{email_text}

REPLY (JSON only):"""
        else:
            final_prompt = prompt + "\n\nEMAIL:\n" + email_text

        resp = self._call(final_prompt)
        if not resp:
            return {"subject": "", "body": "Thanks for your email. I'll get back to you soon."}

        parsed = safe_json_extract(resp)
        if isinstance(parsed, dict):
            return {"subject": parsed.get("subject", ""), "body": parsed.get("body", "")}
        return {"subject": "", "body": resp.strip()}

    # ------------------------------
    # Chat with Email Context - IMPROVED
    # ------------------------------
    def chat_with_email(self, email_text: str, user_query: str, prompt: Optional[str] = None):
        if prompt is None:
            # IMPROVED DEFAULT PROMPT
            final_prompt = f"""You are an intelligent email assistant. Answer the user's question based ONLY on the email content provided.

EMAIL CONTENT:
{email_text}

USER QUESTION:
{user_query}

ANSWER:"""
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
        client = getattr(llm_service, "client", None)
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

    try:
        # For google-genai SDK 1.x: response.text
        text = getattr(response, "text", None)
        if text:
            return text if isinstance(text, str) else str(text)

        # Try candidates[0].content.parts[0].text (common in new SDK)
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                parts = cand.content.parts
                if parts and len(parts) > 0:
                    part_text = getattr(parts[0], "text", None)
                    if part_text:
                        return part_text

        # Fallback: str(response)
        return str(response)
    except Exception:
        logger.exception("Failed to extract text from response object.")
        return None

# ---------------------------------------------------------
# GLOBAL INSTANCE (safe to import)
# ---------------------------------------------------------
llm_service = LLMService()