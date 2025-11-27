# backend/src/routers/agent.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any, Dict
from sqlmodel import select
from ..db import get_session
from ..models import Email, EmailProcessing, Prompt, Draft
from src.services.llm_service import llm_service as llm
import traceback
import logging



logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

class ChatRequest(BaseModel):
    email_id: Optional[int] = None
    query: str
    prompt_key: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    metadata: Optional[Dict[str, Any]] = None

class DraftRequest(BaseModel):
    email_id: int
    tone: Optional[str] = "friendly"
    prompt_key: Optional[str] = "auto_reply"


@router.post("/chat")
def chat_agent(payload: ChatRequest, request: Request):
    # FIX: Do NOT call llm(), llm is already an instance.
    llm_service_instance = llm
    
    session = get_session()
    try:
        context_text = ""
        if payload.email_id:
            email = session.get(Email, payload.email_id)
            if not email:
                raise HTTPException(status_code=404, detail="Email not found")

            proc = session.exec(
                select(EmailProcessing).where(EmailProcessing.email_id == email.id)
            ).first()

            tasks = proc.tasks_json if proc else None
            context_text = (
                f"Subject: {email.subject}\nFrom: {email.sender}\n\n"
                f"{email.body}\n\nExtracted tasks: {tasks}"
            )
        else:
            emails = session.exec(select(Email)).all()
            context_text = "Inbox summary:\n" + "\n".join(
                [f"- {e.subject} (from {e.sender})" for e in emails[:10]]
            )

        prompt_text = None
        if payload.prompt_key:
            p = session.get(Prompt, payload.prompt_key)
            if p:
                prompt_text = p.text

        # FIX: use instance
        reply = llm_service_instance.chat_with_email(
            context_text, payload.query, prompt=prompt_text
        )
        return {"reply": reply, "metadata": {"email_id": payload.email_id}}

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Agent /chat error")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e), "traceback": tb}
        )
    finally:
        session.close()


@router.post("/draft")
def generate_draft(req: DraftRequest, request: Request, save: bool = Query(False)):
    """
    Generate a draft for an email.
    By default this returns a preview and DOES NOT save to DB.
    If you pass ?save=true (or save=True in query) it will persist.
    """
    llm_service_instance = llm

    session = get_session()
    try:
        email = session.get(Email, req.email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        prompt_text = None
        p = session.get(Prompt, req.prompt_key) if req.prompt_key else None
        if p:
            prompt_text = p.text

        # Use the llm instance to generate the draft content
        draft_obj = llm_service_instance.generate_reply(
            email.body, prompt=prompt_text, tone=req.tone
        )

        # Build draft response
        response_draft = {
            "email_id": email.id,
            "subject": draft_obj.get("subject") or f"Re: {email.subject}",
            "body": draft_obj.get("body") or "",
        }

        # Persist only if save flag is true
        if save:
            d = Draft(
                email_id=email.id,
                subject=response_draft["subject"],
                body=response_draft["body"],
            )
            session.add(d)
            session.commit()
            session.refresh(d)
            response_draft["id"] = d.id
            response_draft["saved"] = True
        else:
            response_draft["saved"] = False

        return {"draft": response_draft}

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Agent /draft error")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e), "traceback": tb}
        )
    finally:
        session.close()