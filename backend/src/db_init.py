# backend/src/db_init.py
from src.database import engine
# Import your Base where you declare SQLAlchemy models
# Example: from src.models import Base
try:
    from src.models import Base
except Exception:
    # If your models module is named differently, update the import above
    raise

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("SQLite DB file checked/created.")
