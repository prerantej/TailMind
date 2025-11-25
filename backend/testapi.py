import os
from dotenv import load_dotenv

# FORCE dotenv to load from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("Loading .env from:", env_path)
load_dotenv(env_path)

print("Current Working Directory:", os.getcwd())
print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))
