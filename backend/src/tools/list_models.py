# backend/src/tools/list_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Use the same .env loading approach that works in your environment:
# load the .env file that lives next to this script (i.e. backend/src/.env)
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("Loading .env from:", env_path)
load_dotenv(env_path)

# now configure the SDK and list models
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in " + env_path)

genai.configure(api_key=api_key)

print("Calling list_models() with your API key...")
try:
    models = genai.list_models()
    print("Available models (first 50):")
    for m in list(models)[:50]:
        print(m)
except Exception as e:
    print("list_models() threw an exception:", repr(e))
    # fallback: try to print something informative
    try:
        client = genai._client
        print("genai._client available:", client)
    except Exception:
        print("Could not access genai client internals.")
