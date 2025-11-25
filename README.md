# Email Productivity Agent - Starter Project

This repository is a starter skeleton for the Prompt-Driven Email Productivity Agent assignment.
It includes a minimal FastAPI backend and a minimal React frontend (Vite).

**Assignment spec included:** `assignment-spec.pdf`

## Quickstart (local)

### Backend
1. Python 3.10+ recommended.
2. Create and activate a virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .\.venv\Scripts\activate  # Windows (Powershell)
   ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Run the backend:
   ```bash
   cd backend
   uvicorn src.main:app --reload --port 8000
   ```
5. Backend will create a local SQLite DB at `backend/src/data/email_agent.db`.

### Frontend
1. Node 16+ installed.
2. From repo root:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open http://localhost:5173 and use the UI.

## How to use (demo)
1. Start backend and frontend.
2. Open frontend page.
3. Click **Load Mock Inbox** to populate emails (calls `POST /inbox/load`).
4. Inbox list will show emails and categories.
5. Edit prompts in the Prompt Brain panel and click Save.

## Notes
- LLM integration: The backend includes a simple `LLMService` that uses heuristics if `OPENAI_API_KEY` is not set. To enable real OpenAI calls, set `OPENAI_API_KEY` in your environment.
- This is a starter skeleton. Expand `src/services/llm_service.py` to hook into OpenAI or other LLMs, and implement more endpoints as needed.

