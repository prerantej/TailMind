# backend/src/db_init.py
"""
Initialization helper for Render startup.
This simply calls your existing utility that sets up tables.
"""

from src.db import create_db_and_tables

def init_db():
    create_db_and_tables()

if __name__ == "__main__":
    init_db()
    print("DB checked/created using create_db_and_tables().")
