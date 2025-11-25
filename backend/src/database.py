# backend/src/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/dev.db")

# If using SQLite file (local dev), keep check_same_thread and NullPool
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        poolclass=NullPool,
    )
else:
    # For Postgres (and other production DBs)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Optional helper for dependency injection in FastAPI
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
