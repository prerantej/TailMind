# backend/src/main.py
import os
from dotenv import load_dotenv
import logging
import traceback
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlmodel import select
import traceback as _traceback
from pydantic import BaseModel

from .services.llm_service import safe_json_extract

# --- load .env (resolve relative to this file -> backend/.env) ---
BASE_DIR = Path(__file__).resolve().parent  # backend/src
env_path = BASE_DIR.parent / ".env"         # backend/.env
print("Loading .env from:", env_path)
load_dotenv(env_path)

# --- logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email-agent-backend")

# --- import DB, models, services ---
from .db import engine, create_db_and_tables, get_session
from .models import Email, EmailProcessing, Prompt, Draft
from .services.ingestion_service import load_and_process_inbox

# Import global LLM service instance
try:
    from .services.llm_service import llm_service as llm
except Exception:
    logger.exception(
        "Failed to import llm_service. Make sure GEMINI_API_KEY is set correctly."
    )
    raise

# --- Create DB tables if they don't exist ---
create_db_and_tables()

# --- FastAPI app ---
app = FastAPI(title="Email Productivity Agent - Backend")

# ------------------------------------------------------------------
# ✅ PRODUCTION CORS CONFIGURATION
# ------------------------------------------------------------------
# Set this on Render:
# FRONTEND_URL = https://your-frontend.vercel.app
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

allowed_origins = [FRONTEND_URL] if FRONTEND_URL != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Routers (if any)
# ------------------------------------------------------------------
try:
    from .routers.agent import router as agent_router
    app.include_router(agent_router)
except Exception:
    logger.debug("Router import failed or not present. Continuing without router.")

# ------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------
class DraftCreate(BaseModel):
    email_id: int
    subject: str
    body: str

class BatchDelete(BaseModel):
    ids: List[int]

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.post("/inbox/load")
async def inbox_load(mock: bool = True, reset: bool = Query(False)):
    try:
        processed = load_and_process_inbox(engine, llm)
        return {"status": "ok", "result": processed}
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("INGESTION ERROR")
        return {"status": "error", "error": str(e), "traceback": tb}


@app.get("/inbox")
def get_inbox():
    with get_session() as session:
        emails = session.exec(select(Email)).all()
        results = []
        for e in emails:
            proc = session.exec(
                select(EmailProcessing).where(EmailProcessing.email_id == e.id)
            ).first()
            results.append(
                {
                    "id": e.id,
                    "sender": e.sender,
                    "subject": e.subject,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "category": proc.category if proc else None,
                }
            )
        return results


@app.get("/email/{email_id}")
def get_email(email_id: int):
    with get_session() as session:
        e = session.get(Email, email_id)
        if not e:
            raise HTTPException(status_code=404, detail="Email not found")
        proc = session.exec(
            select(EmailProcessing).where(EmailProcessing.email_id == e.id)
        ).first()
        return {"email": e.dict(), "processing": proc.dict() if proc else None}


@app.get("/prompts")
def get_prompts():
    with get_session() as session:
        prompts = session.exec(select(Prompt)).all()
        return {p.key: p.text for p in prompts}


@app.post("/prompts/update")
def update_prompt(key: str, text: str):
    with get_session() as session:
        p = session.get(Prompt, key)
        if p:
            p.text = text
            session.add(p)
            session.commit()
            return {"status": "updated"}
        else:
            new = Prompt(key=key, text=text)
            session.add(new)
            session.commit()
            return {"status": "created"}


@app.post("/agent/draft")
def generate_draft(email_id: int, tone: str = "friendly"):
    with get_session() as session:
        email = session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        prompt_obj = session.get(Prompt, "auto_reply")
        prompt_text = prompt_obj.text if prompt_obj else None

        try:
            draft = llm.generate_reply(email.body, prompt_text, tone=tone)
        except Exception:
            logger.exception("LLM generate_reply failed, returning fallback draft.")
            draft = {"subject": "", "body": "Thanks — will follow up soon."}

        subject = ""
        body = ""

        if isinstance(draft, dict):
            subject = draft.get("subject", "") or ""
            body = draft.get("body", "") or ""
        elif isinstance(draft, str):
            parsed = None
            try:
                parsed = safe_json_extract(draft)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                subject = parsed.get("subject", "") or ""
                body = parsed.get("body", "") or ""
            else:
                body = draft
        else:
            body = str(draft)

        if not subject:
            subject = f"Re: {email.subject}"

        return {"draft": {"email_id": email.id, "subject": subject.strip(), "body": body.strip()}}


@app.post("/draft/save")
def save_draft(payload: DraftCreate):
    with get_session() as session:
        email = session.get(Email, payload.email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        subj = (payload.subject or "").strip()
        bod = (payload.body or "").strip()
        if not bod:
            raise HTTPException(status_code=400, detail="Draft body cannot be empty")

        d = Draft(email_id=email.id, subject=subj, body=bod)
        session.add(d)
        session.commit()
        session.refresh(d)
        return {"status": "saved", "draft": d.dict()}


@app.get("/draft/{draft_id}")
def get_draft(draft_id: int):
    with get_session() as session:
        d = session.get(Draft, draft_id)
        if not d:
            raise HTTPException(status_code=404, detail="Draft not found")
        email = session.get(Email, d.email_id)
        return {"draft": d.dict(), "email": email.dict() if email else None}


@app.delete("/draft/{draft_id}")
def delete_draft(draft_id: int):
    with get_session() as session:
        d = session.get(Draft, draft_id)
        if not d:
            raise HTTPException(status_code=404, detail="Draft not found")
        session.delete(d)
        session.commit()
        return {"status": "deleted", "id": draft_id}


@app.delete("/drafts/batch-delete")
def batch_delete(payload: BatchDelete):
    with get_session() as session:
        deleted_ids = []
        for draft_id in payload.ids:
            d = session.get(Draft, draft_id)
            if d:
                session.delete(d)
                deleted_ids.append(draft_id)
        session.commit()
        return {"status": "deleted", "deleted_ids": deleted_ids}


@app.get("/drafts")
def list_drafts():
    with get_session() as session:
        drafts = session.exec(select(Draft)).all()
        return [d.dict() for d in drafts]


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
