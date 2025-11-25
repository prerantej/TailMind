# backend/seed_prompts.py
from src.db import get_session, create_db_and_tables
from src.models import Prompt

create_db_and_tables()

prompts = {
    "categorization": "Read the email and categorize it into one of these: Important, To-Do, Newsletter, or Spam. Pick the best category based only on the email. Reply with just the category.",
    "action_extraction": "Find what the email is asking the user to do. Write the tasks clearly and briefly.\nReturn a JSON list like this:\n[\n  { \"task\": \"…\", \"deadline\": \"…\" }\n]\n\nIf you can't find any tasks, return [].",
    "auto_reply": "Write a short, polite reply to the email. Be helpful and clear.\nReturn JSON:\n{ \"subject\": \"...\", \"body\": \"...\" }"
}

with get_session() as session:
    for k, v in prompts.items():
        existing = session.get(Prompt, k)
        if existing:
            existing.text = v
            session.add(existing)
        else:
            session.add(Prompt(key=k, text=v))
    session.commit()
    print("Prompts seeded/updated.")
