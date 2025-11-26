# backend/src/services/ingestion_service.py
import json
import re
import logging
from datetime import datetime
from typing import Optional, List

from sqlmodel import select

from ..db import get_session
from ..models import Email, EmailProcessing
from .llm_service import LLMService

logger = logging.getLogger(__name__)

def _parse_iso(dt_str: str):
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%d")
            except Exception:
                return datetime.utcnow()

def _strip_code_fences(text: str):
    if not text:
        return text
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text

def _extract_first_json_array(text: str):
    """
    Try to extract first JSON array (e.g. [ {...}, {...} ]) from model output.
    Returns parsed list or None.
    """
    if not text:
        return None
    t = _strip_code_fences(text)
    # find first [...] JSON array block
    m = re.search(r"(\[\s*{.*?}\s*\])", t, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # try parse whole text as JSON
    try:
        parsed = json.loads(t)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return None

def _normalize_parsed_item(item):
    """
    Ensure an item becomes a dict with keys: task, deadline, source
    """
    if isinstance(item, dict):
        task_text = item.get("task") or item.get("text") or item.get("fragment") or str(item)
        deadline = item.get("deadline") if item.get("deadline") else None
    else:
        task_text = str(item)
        deadline = None
    return {"task": task_text, "deadline": deadline, "source": "llm"}

def _parse_llm_tasks(raw_tasks) -> List[dict]:
    """
    Normalize whatever the LLM returns into a list of task dicts.
    """
    normalized = []
    if isinstance(raw_tasks, list):
        for r in raw_tasks:
            normalized.append(_normalize_parsed_item(r))
    elif isinstance(raw_tasks, dict):
        normalized.append(_normalize_parsed_item(raw_tasks))
    elif isinstance(raw_tasks, str):
        parsed = _extract_first_json_array(raw_tasks)
        if parsed:
            for p in parsed:
                normalized.append(_normalize_parsed_item(p))
        else:
            # fallback: split lines and use them as tasks or store raw
            lines = [ln.strip() for ln in raw_tasks.splitlines() if ln.strip()]
            if len(lines) > 1:
                for ln in lines:
                    normalized.append({"task": ln, "deadline": None, "source": "llm"})
            elif len(lines) == 1:
                normalized.append({"task": lines[0], "deadline": None, "source": "llm"})
            else:
                normalized.append({"task": f"RAW_LLM_OUTPUT: {raw_tasks}", "deadline": None, "source": "llm_raw"})
    else:
        normalized = []
    return normalized

def load_and_process_inbox(engine, llm: LLMService, reset: bool = False):
    """
    Process emails from the `email` table and populate `emailprocessing`.
    - If reset==False (default), only process emails that do NOT have an EmailProcessing row yet.
    - If reset==True, re-process all emails (updates existing EmailProcessing rows).
    Returns a dict with status, counts and errors.
    """
    session = get_session()
    processed = 0
    errors = []

    try:
        # fetch emails to process
        if reset:
            emails = session.exec(select(Email)).all()
        else:
            # select emails where no processing row exists
            all_emails = session.exec(select(Email)).all()
            emails = []
            for e in all_emails:
                exists = session.exec(select(EmailProcessing).where(EmailProcessing.email_id == e.id)).first()
                if not exists:
                    emails.append(e)

        logger.info("Ingestion: %s emails to process (reset=%s)", len(emails), reset)

        for e in emails:
            try:
                # Build LLM input: subject + body + optional metadata
                llm_input = f"Subject: {e.subject}\n\n{e.body or ''}"

                # Categorize
                try:
                    category = llm.categorize(llm_input) or "uncategorized"
                except Exception:
                    logger.exception("LLM categorize failed for email id %s", e.id)
                    category = "uncategorized"

                # Extract tasks
                try:
                    raw_tasks = llm.extract_tasks(llm_input)
                except Exception as ex_llm:
                    logger.exception("LLM extract_tasks failed for email id %s: %s", e.id, ex_llm)
                    raw_tasks = None

                logger.debug("LLM raw tasks for email_id=%s: %r", e.id, raw_tasks)

                normalized = _parse_llm_tasks(raw_tasks)

                # Prepare EmailProcessing entry (insert or update)
                existing = session.exec(select(EmailProcessing).where(EmailProcessing.email_id == e.id)).first()
                if existing:
                    existing.category = category
                    existing.tasks_json = json.dumps(normalized, ensure_ascii=False)
                    # preserve existing draft_json unless you want to reset it here
                    session.add(existing)
                    logger.info("Updated EmailProcessing for email_id=%s", e.id)
                else:
                    proc = EmailProcessing(
                        email_id=e.id,
                        category=category,
                        tasks_json=json.dumps(normalized, ensure_ascii=False),
                        draft_json=None
                    )
                    session.add(proc)
                    logger.info("Inserted EmailProcessing for email_id=%s", e.id)

                session.commit()
                processed += 1

            except Exception as ex_item:
                logger.exception("Error processing email id %s: %s", getattr(e, "id", "unknown"), ex_item)
                errors.append(f"email_id={getattr(e, 'id', None)}, error={str(ex_item)}")
                session.rollback()
                continue

    finally:
        session.close()

    return {"status": "ok", "processed": processed, "errors": errors}
