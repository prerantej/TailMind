from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime

class Email(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    recipients: Optional[str] = None
    subject: str
    body: str
    timestamp: datetime

class EmailProcessing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: int = Field(foreign_key="email.id")
    category: Optional[str] = None
    tasks_json: Optional[str] = None
    draft_json: Optional[str] = None

class Prompt(SQLModel, table=True):
    key: str = Field(primary_key=True)
    text: str

class Draft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email_id: Optional[int] = Field(foreign_key="email.id")
    subject: str
    body: str
