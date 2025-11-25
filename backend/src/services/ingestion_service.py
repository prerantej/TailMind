# backend/src/services/ingestion_service.py
import json
import re
import logging
from pathlib import Path
from datetime import datetime

from ..db import get_session
from ..models import Email, EmailProcessing
from .llm_service import LLMService, llm_service
from sqlmodel import delete

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

def load_and_process_inbox(engine, llm: LLMService):
    """
    Simple ingestion: hand the email text to the LLM and accept its output.
    Minimal parsing only. Keep raw LLM output when parsing fails so UI can show it.
    """
    data_file = Path(__file__).resolve().parents[1] / 'data' / 'mock_inbox.json'
    if not data_file.exists():
        return {"status": "no_file", "processed": 0, "errors": ["mock_inbox.json not found"]}

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            emails = json.load(f)
    except Exception as e:
        return {"status": "bad_json", "processed": 0, "errors": [str(e)]}

    session = get_session()
    processed = 0
    errors = []

    try:
        # clear demo data
        session.exec(delete(EmailProcessing))
        session.exec(delete(Email))
        session.commit()

        for idx, item in enumerate(emails):
            try:
                sender = (item.get('sender') or '').strip()
                subject = (item.get('subject') or '').strip() or '(no subject)'
                body = item.get('body') or ''
                raw_ts = item.get('timestamp')
                timestamp = _parse_iso(raw_ts) if raw_ts else datetime.utcnow()

                # persist email row
                e = Email(sender=sender, recipients=item.get('recipients'),
                          subject=subject, body=body, timestamp=timestamp)
                session.add(e)
                session.commit()
                session.refresh(e)

                # single LLM prompt input (give full context)
                llm_input = f"Subject: {subject}\n\n{body}"

                # Primary LLM calls (single-step approach)
                try:
                    category = llm.categorize(llm_input) or "uncategorized"
                except Exception:
                    logger.exception("LLM categorize failed for email id %s", e.id)
                    category = "uncategorized"

                # Extract tasks
                raw_tasks = None
                try:
                    raw_tasks = llm.extract_tasks(llm_input)
                except Exception as ex_llm:
                    logger.exception("LLM extract_tasks failed for email id %s: %s", e.id, ex_llm)
                    raw_tasks = None

                logger.debug("LLM raw task output for email_id=%s: %r", e.id, raw_tasks)

                normalized = []

                # If model returned a list/dict directly (python object), normalize
                if isinstance(raw_tasks, list):
                    for r in raw_tasks:
                        normalized.append(_normalize_parsed_item(r))
                elif isinstance(raw_tasks, dict):
                    normalized.append(_normalize_parsed_item(raw_tasks))
                elif isinstance(raw_tasks, str):
                    # try to extract a JSON array contained in the string
                    parsed = _extract_first_json_array(raw_tasks)
                    if parsed:
                        for p in parsed:
                            normalized.append(_normalize_parsed_item(p))
                    else:
                        # fallback: store the raw LLM string as a single task so UI shows it
                        # but also try newline splitting if it looks like list lines
                        lines = [ln.strip() for ln in raw_tasks.splitlines() if ln.strip()]
                        if len(lines) > 1:
                            for ln in lines:
                                normalized.append({"task": ln, "deadline": None, "source": "llm"})
                        elif len(lines) == 1:
                            # single-line freeform output; store as one task
                            normalized.append({"task": lines[0], "deadline": None, "source": "llm"})
                        else:
                            # nothing parsed; store raw LLM output as debug fallback
                            normalized.append({"task": f"RAW_LLM_OUTPUT: {raw_tasks}", "deadline": None, "source": "llm_raw"})
                else:
                    # model returned None or unknown type -> keep empty list
                    normalized = []

                # Ensure tasks_json is always a JSON array in DB
                proc = EmailProcessing(email_id=e.id, category=category, tasks_json=json.dumps(normalized, ensure_ascii=False))
                session.add(proc)
                session.commit()

                processed += 1

            except Exception as ex_item:
                logger.exception("Error processing item index %s: %s", idx, ex_item)
                errors.append(f"item_index={idx}, error={str(ex_item)}")
                session.rollback()
                continue

    finally:
        session.close()

    return {"status": "ok", "processed": processed, "errors": errors}
