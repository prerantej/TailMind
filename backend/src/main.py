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
            
            email_dict = {
                "id": email.id,
                "sender": email.sender,
                "recipients": email.recipients,
                "subject": email.subject,
                "body": email.body,
                "timestamp": email.timestamp.isoformat(),
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
        
        return {
            "id": email.id,
            "sender": email.sender,
            "recipients": email.recipients,
            "subject": email.subject,
            "body": email.body,
            "timestamp": email.timestamp.isoformat(),
            "category": processing.category if processing else None,
            "tasks": processing.tasks_json if processing else None,
            "draft": processing.draft_json if processing else None
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
            result.append({
                "id": draft.id,
                "email_id": draft.email_id,
                "subject": draft.subject,
                "body": draft.body,
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
        
        return {
            "id": draft.id,
            "email_id": draft.email_id,
            "subject": draft.subject,
            "body": draft.body
        }

# ==================== Prompt Routes ====================

@app.get("/prompts")
async def get_all_prompts():
    """Get all prompts"""
    with get_session() as session:
        prompts = session.exec(select(Prompt)).all()
        return {
            "prompts": [{"key": p.key, "text": p.text} for p in prompts]
        }

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

@app.post("/process/reprocess")
async def reprocess_emails():
    """Reprocess all emails with current prompts"""
    with get_session() as session:
        result = load_and_process_inbox(session.get_bind(), llm_service, reset=True)
        return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)