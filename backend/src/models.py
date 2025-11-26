# backend/src/models.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Email(SQLModel, table=True):
    """Email model - stores incoming emails"""
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str = Field(index=True)
    recipients: Optional[str] = None
    subject: str
    body: str
    timestamp: datetime = Field(default_factory=datetime.now, index=True)

class EmailProcessing(SQLModel, table=True):
    """EmailProcessing model - stores LLM processing results"""
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: int = Field(foreign_key="email.id", index=True, unique=True)
    category: Optional[str] = None
    tasks_json: Optional[str] = None  # JSON string of tasks
    draft_json: Optional[str] = None  # JSON string of draft

class Prompt(SQLModel, table=True):
    """Prompt model - stores customizable LLM prompts"""
    key: str = Field(primary_key=True)
    text: str

class Draft(SQLModel, table=True):
    """Draft model - stores generated email drafts"""
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: Optional[int] = Field(foreign_key="email.id", index=True)
    subject: str
    body: str
    # Note: created_at removed to match existing database schema