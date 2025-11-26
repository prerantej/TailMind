# backend/src/main.py
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session
from pydantic import BaseModel

from .db import create_db_and_tables, get_session
from .models import Email, EmailProcessing, Prompt, Draft
from .services.llm_service import llm_service, _maybe_aclose_client
from .services.ingestion_service import load_and_process_inbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Lifecycle ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting TailMind API...")
    create_db_and_tables()
    logger.info("✅ Database initialized")
    
    # Initialize default prompts if they don't exist
    _initialize_default_prompts()
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down TailMind API...")
    await _maybe_aclose_client()

def _initialize_default_prompts():
    """Initialize default prompts in the database"""
    with get_session() as session:
        default_prompts = {
            "categorization": """You are an email categorization assistant. Analyze the email and respond with ONLY ONE of these categories:
- Important (urgent work, meetings, deadlines)
- Newsletter (marketing, updates, subscriptions)
- Spam (unwanted, promotional)
- To-Do (tasks, action items)

Reply with just the category name, nothing else.""",
            
            "action_extraction": """You are a task extraction assistant. Analyze the email and extract all actionable tasks.
Return a JSON array of tasks in this exact format:
[
  {"task": "description of task", "deadline": "YYYY-MM-DD or null"},
  {"task": "another task", "deadline": null}
]

If there are no tasks, return an empty array: []""",
            
            "auto_reply": """You are an email reply assistant. Write a professional reply to this email.
Return a JSON object in this exact format:
{
  "subject": "Re: [original subject]",
  "body": "your professional reply here"
}"""
        }
        
        for key, text in default_prompts.items():
            existing = session.get(Prompt, key)
            if not existing:
                prompt = Prompt(key=key, text=text)
                session.add(prompt)
                logger.info(f"✅ Created default prompt: {key}")
        
        session.commit()

# ==================== FastAPI App ====================
app = FastAPI(
    title="TailMind API",
    description="Smart inbox with AI agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Pydantic Models ====================
class ChatRequest(BaseModel):
    email_id: int
    user_message: str

class DraftRequest(BaseModel):
    email_id: int
    tone: Optional[str] = "polite"

class PromptUpdateRequest(BaseModel):
    text: str

# ==================== Routes ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "TailMind API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "llm": "available" if llm_service.client else "unavailable"
    }

# ==================== Email Routes ====================

@app.get("/inbox")
async def get_inbox():
    """Get all emails with their processing data"""
    with get_session() as session:
        # Get all emails
        emails = session.exec(select(Email).order_by(Email.timestamp.desc())).all()
        
        result = []
        for email in emails:
            # Get processing data for this email
            processing = session.exec(
                select(EmailProcessing).where(EmailProcessing.email_id == email.id)
            ).first()
            
            # Handle timestamp - it might be datetime or string
            timestamp_str = email.timestamp
            if isinstance(email.timestamp, datetime):
                timestamp_str = email.timestamp.isoformat()
            elif isinstance(email.timestamp, str):
                timestamp_str = email.timestamp
            else:
                timestamp_str = str(email.timestamp)
            
            email_dict = {
                "id": email.id,
                "sender": email.sender,
                "recipients": email.recipients,
                "subject": email.subject,
                "body": email.body,
                "timestamp": timestamp_str,
                "category": processing.category if processing else None,
                "tasks": processing.tasks_json if processing else None,
                "draft": processing.draft_json if processing else None
            }
            result.append(email_dict)
        
        logger.info(f"📧 Returning {len(result)} emails from inbox")
        return {"emails": result, "count": len(result)}

@app.post("/inbox/load")
async def load_mock_emails():
    """Load mock emails into the database"""
    with get_session() as session:
        # Check if emails already exist
        existing_count = len(session.exec(select(Email)).all())
        if existing_count > 0:
            logger.info(f"⚠️ Database already has {existing_count} emails")
            return {
                "message": f"Database already contains {existing_count} emails",
                "count": existing_count
            }
        
        # Create mock emails
        mock_emails = [
            Email(
                sender="boss@company.com",
                recipients="you@company.com",
                subject="Urgent: Q4 Project Deadline",
                body="We need to finalize the Q4 project by Friday. Please schedule a meeting with the team to discuss remaining tasks and timeline.",
                timestamp=datetime.now() - timedelta(hours=2)
            ),
            Email(
                sender="newsletter@techcrunch.com",
                recipients="you@company.com",
                subject="Weekly Tech Newsletter - AI Trends",
                body="This week's top stories: New AI models, startup funding, and more. Click here to unsubscribe from future emails.",
                timestamp=datetime.now() - timedelta(hours=5)
            ),
            Email(
                sender="noreply@promotion.com",
                recipients="you@company.com",
                subject="🎉 HUGE SALE! Buy Now and Save 70%",
                body="Limited time offer! Click here now to claim your discount. Free shipping on all orders. Don't miss out!",
                timestamp=datetime.now() - timedelta(hours=8)
            ),
            Email(
                sender="client@important.com",
                recipients="you@company.com",
                subject="Follow-up: Contract Review",
                body="Hi, just following up on the contract we discussed. Can you please review the attached document and send your feedback by Wednesday? Thanks!",
                timestamp=datetime.now() - timedelta(hours=12)
            ),
            Email(
                sender="hr@company.com",
                recipients="you@company.com",
                subject="Action Required: Annual Performance Review",
                body="Your annual performance review is due next week. Please complete the self-assessment form and submit it to your manager by Monday.",
                timestamp=datetime.now() - timedelta(days=1)
            ),
            Email(
                sender="team@slack.com",
                recipients="you@company.com",
                subject="Your Slack Digest",
                body="You have 15 unread messages in your workspace. Check out what you missed today!",
                timestamp=datetime.now() - timedelta(days=2)
            ),
        ]
        
        for email in mock_emails:
            session.add(email)
        
        session.commit()
        
        # Refresh to get IDs
        for email in mock_emails:
            session.refresh(email)
        
        logger.info(f"✅ Loaded {len(mock_emails)} mock emails")
        
        # Now process them with LLM
        result = load_and_process_inbox(session.get_bind(), llm_service, reset=False)
        
        return {
            "message": f"Loaded and processed {len(mock_emails)} mock emails",
            "count": len(mock_emails),
            "processing_result": result
        }

@app.get("/email/{email_id}")
async def get_email_detail(email_id: int):
    """Get detailed information about a specific email"""
    with get_session() as session:
        email = session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        processing = session.exec(
            select(EmailProcessing).where(EmailProcessing.email_id == email_id)
        ).first()
        
        # Handle timestamp - it might be datetime or string
        timestamp_str = email.timestamp
        if isinstance(email.timestamp, datetime):
            timestamp_str = email.timestamp.isoformat()
        elif isinstance(email.timestamp, str):
            timestamp_str = email.timestamp
        else:
            timestamp_str = str(email.timestamp)
        
        # Return format that EmailDetail.jsx expects
        return {
            "email": {
                "id": email.id,
                "sender": email.sender,
                "recipients": email.recipients,
                "subject": email.subject,
                "body": email.body,
                "timestamp": timestamp_str
            },
            "processing": {
                "category": processing.category if processing else None,
                "tasks_json": processing.tasks_json if processing else None,
                "draft_json": processing.draft_json if processing else None
            } if processing else None
        }

# ==================== Chat Routes ====================

@app.post("/chat")
async def chat_with_email(request: ChatRequest):
    """Chat about a specific email using LLM"""
    with get_session() as session:
        email = session.get(Email, request.email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        email_text = f"Subject: {email.subject}\n\n{email.body}"
        response = llm_service.chat_with_email(email_text, request.user_message)
        
        return {"response": response}

@app.post("/agent/chat")
async def agent_chat(request: dict):
    """Agent chat endpoint - handles chat with or without email context"""
    email_id = request.get("email_id")
    query = request.get("query") or request.get("user_message", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    with get_session() as session:
        if email_id:
            email = session.get(Email, email_id)
            if email:
                email_text = f"Subject: {email.subject}\n\n{email.body}"
                response = llm_service.chat_with_email(email_text, query)
            else:
                response = "Email not found"
        else:
            # General query without email context
            response = llm_service._call(query) or "LLM unavailable"
        
        return {"reply": response}

@app.post("/agent/draft")
async def agent_generate_draft(request: dict):
    """Agent draft generation endpoint"""
    email_id = request.get("email_id")
    tone = request.get("tone", "polite")
    
    if not email_id:
        raise HTTPException(status_code=400, detail="email_id is required")
    
    with get_session() as session:
        email = session.get(Email, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        email_text = f"Subject: {email.subject}\n\n{email.body}"
        draft_data = llm_service.generate_reply(email_text, tone=tone)
        
        # Save draft
        draft = Draft(
            email_id=email.id,
            subject=draft_data.get("subject", ""),
            body=draft_data.get("body", "")
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
        
        logger.info(f"✅ Generated draft for email {email.id}")
        
        return {
            "draft": {
                "id": draft.id,
                "email_id": draft.email_id,
                "subject": draft.subject,
                "body": draft.body
            }
        }

# ==================== Draft Routes ====================

@app.post("/draft/generate")
async def generate_draft(request: DraftRequest):
    """Generate a draft reply for an email"""
    with get_session() as session:
        email = session.get(Email, request.email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        email_text = f"Subject: {email.subject}\n\n{email.body}"
        draft_data = llm_service.generate_reply(email_text, tone=request.tone)
        
        # Save draft
        draft = Draft(
            email_id=email.id,
            subject=draft_data.get("subject", ""),
            body=draft_data.get("body", "")
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
        
        logger.info(f"✅ Generated draft for email {email.id}")
        
        return {
            "draft_id": draft.id,
            "subject": draft.subject,
            "body": draft.body
        }

@app.get("/drafts")
async def get_all_drafts():
    """Get all saved drafts"""
    with get_session() as session:
        drafts = session.exec(select(Draft)).all()
        
        result = []
        for draft in drafts:
            email = session.get(Email, draft.email_id) if draft.email_id else None
            
            # Handle created_at if it exists, otherwise use current time
            created_at_str = None
            if hasattr(draft, 'created_at') and draft.created_at:
                if isinstance(draft.created_at, datetime):
                    created_at_str = draft.created_at.isoformat()
                else:
                    created_at_str = str(draft.created_at)
            
            result.append({
                "id": draft.id,
                "email_id": draft.email_id,
                "subject": draft.subject,
                "body": draft.body,
                "created_at": created_at_str,
                "original_subject": email.subject if email else None
            })
        
        return {"drafts": result, "count": len(result)}

@app.get("/draft/{draft_id}")
async def get_draft(draft_id: int):
    """Get a specific draft"""
    with get_session() as session:
        draft = session.get(Draft, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        email = session.get(Email, draft.email_id) if draft.email_id else None
        
        # Handle created_at
        created_at_str = None
        if hasattr(draft, 'created_at') and draft.created_at:
            if isinstance(draft.created_at, datetime):
                created_at_str = draft.created_at.isoformat()
            else:
                created_at_str = str(draft.created_at)
        
        return {
            "draft": {
                "id": draft.id,
                "email_id": draft.email_id,
                "subject": draft.subject,
                "body": draft.body,
                "created_at": created_at_str
            },
            "email": {
                "id": email.id,
                "subject": email.subject,
                "body": email.body,
                "sender": email.sender,
                "timestamp": email.timestamp.isoformat() if isinstance(email.timestamp, datetime) else str(email.timestamp)
            } if email else None
        }

@app.post("/draft/save")
async def save_draft(request: dict):
    """Save or update a draft"""
    email_id = request.get("email_id")
    subject = request.get("subject", "")
    body = request.get("body", "")
    
    with get_session() as session:
        draft = Draft(
            email_id=email_id,
            subject=subject,
            body=body
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
        
        return {
            "status": "saved",
            "draft": {
                "id": draft.id,
                "email_id": draft.email_id,
                "subject": draft.subject,
                "body": draft.body
            }
        }

@app.delete("/draft/{draft_id}")
async def delete_draft(draft_id: int):
    """Delete a specific draft"""
    with get_session() as session:
        draft = session.get(Draft, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        session.delete(draft)
        session.commit()
        
        return {"status": "deleted", "id": draft_id}

@app.delete("/drafts/batch-delete")
async def batch_delete_drafts(request: dict):
    """Delete multiple drafts"""
    ids = request.get("ids", [])
    
    with get_session() as session:
        deleted_count = 0
        for draft_id in ids:
            draft = session.get(Draft, draft_id)
            if draft:
                session.delete(draft)
                deleted_count += 1
        
        session.commit()
        
        return {"status": "deleted", "count": deleted_count}

# ==================== Prompt Routes ====================

@app.get("/prompts")
async def get_all_prompts():
    """Get all prompts"""
    with get_session() as session:
        prompts = session.exec(select(Prompt)).all()
        # Return as dict with key: text format
        result = {p.key: p.text for p in prompts}
        return result

@app.get("/prompt/{key}")
async def get_prompt(key: str):
    """Get a specific prompt"""
    with get_session() as session:
        prompt = session.get(Prompt, key)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return {"key": prompt.key, "text": prompt.text}

@app.put("/prompt/{key}")
async def update_prompt(key: str, request: PromptUpdateRequest):
    """Update a prompt"""
    with get_session() as session:
        prompt = session.get(Prompt, key)
        if not prompt:
            # Create new prompt if it doesn't exist
            prompt = Prompt(key=key, text=request.text)
            session.add(prompt)
        else:
            prompt.text = request.text
        
        session.commit()
        session.refresh(prompt)
        
        logger.info(f"✅ Updated prompt: {key}")
        return {"key": prompt.key, "text": prompt.text}

@app.post("/prompts/update")
async def update_prompt_legacy(key: str, text: str):
    """Update a prompt (legacy endpoint for PromptBrain)"""
    with get_session() as session:
        prompt = session.get(Prompt, key)
        if not prompt:
            prompt = Prompt(key=key, text=text)
            session.add(prompt)
        else:
            prompt.text = text
        
        session.commit()
        session.refresh(prompt)
        
        logger.info(f"✅ Updated prompt: {key}")
        return {"status": "ok", "key": prompt.key}

@app.post("/process/reprocess")
async def reprocess_emails():
    """Reprocess all emails with current prompts"""
    with get_session() as session:
        result = load_and_process_inbox(session.get_bind(), llm_service, reset=True)
        return result

@app.delete("/admin/clear-emails")
async def clear_all_emails():
    """Clear all emails and processing data from database"""
    with get_session() as session:
        # Delete all email processing records
        processing_records = session.exec(select(EmailProcessing)).all()
        for record in processing_records:
            session.delete(record)
        
        # Delete all emails
        emails = session.exec(select(Email)).all()
        for email in emails:
            session.delete(email)
        
        # Delete all drafts
        drafts = session.exec(select(Draft)).all()
        for draft in drafts:
            session.delete(draft)
        
        session.commit()
        
        logger.info("🗑️ Cleared all emails, processing data, and drafts")
        return {
            "message": "All emails, processing data, and drafts cleared",
            "deleted": {
                "emails": len(emails),
                "processing": len(processing_records),
                "drafts": len(drafts)
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)