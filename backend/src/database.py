# backend/src/database.py
import os
import logging
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("⚠️ DATABASE_URL not set, using SQLite fallback")
    DATABASE_URL = "sqlite:///./tailmind.db"
else:
    # Render Postgres URLs start with 'postgres://' but SQLAlchemy needs 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        logger.info(f"✅ Using PostgreSQL database")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Maximum number of connections to keep open
    max_overflow=20,  # Maximum number of connections that can be created beyond pool_size
)

def create_db_and_tables():
    """Create all database tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.exception(f"❌ Failed to create database tables: {e}")
        raise

@contextmanager
def get_session():
    """Get a database session (context manager)"""
    session = Session(engine)
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.exception(f"❌ Database session error: {e}")
        raise
    finally:
        session.close()