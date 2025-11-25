from sqlmodel import SQLModel, create_engine, Session
from sqlmodel import Field
from typing import Optional
from datetime import datetime
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[1] / 'data' / 'email_agent.db'
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def create_db_and_tables():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
