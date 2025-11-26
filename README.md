

# 📧 TailMind — Smart Inbox + AI Email Agent

Your intelligent inbox that categorizes emails, extracts tasks, chats with email context, and generates professional drafts — all powered by Gemini LLM.

---

# 🌐 Project Overview

TailMind is a full-stack AI email assistant with:

### ✔️ AI-Based Email Categorization

Automatically classifies emails as **Important**, **Newsletter**, **Spam**, or **To-Do**.

### ✔️ Action Item Extraction

Uses LLM to pull structured tasks out of any email.

### ✔️ Smart Email Chatbox

Chat about any email (“summarize”, “what is the sender asking?”, “generate reply”) with full context awareness.

### ✔️ Auto Draft Generation

One-click reply generation in customizable tones.

### ✔️ Prompt Brain

Editable prompts (categorization / extraction / email reply) stored in DB.

### ✔️ Beautiful Modern UI (React + Tailwind)

Inbox, email detail view, draft manager, chatbox.

---



---

# 🏗️ Tech Stack

### **Frontend**

* React (Vite)
* TailwindCSS / shadcn components
* Axios API client

### **Backend**

* FastAPI
* SQLModel + SQLAlchemy
* PostgreSQL (Render)
* Google Gemini LLM (google-genai or google-generativeai SDK)

---

# 📁 Project Structure

```
root/
│── backend/
│   ├── src/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── ingestion_service.py
│   │   ├── routers/
│   │   │   ├── agent.py
│   ├── requirements.txt
│
│── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── lib/api.js
│   ├── index.html
│
│── README.md
│── .env.example
```

---

# 🔧 Backend Setup

### 1. Install dependencies

```
cd backend
pip install -r requirements.txt
```

### 2. Create `.env` file

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. Run FastAPI server

```
uvicorn src.main:app --reload
```

Backend will run at:

```
http://localhost:8000
```

### 4. Access docs

Swagger:

```
http://localhost:8000/docs
```

ReDoc:

```
http://localhost:8000/redoc
```

---

# 🎨 Frontend Setup

### 1. Install dependencies

```
cd frontend
npm install
```

### 2. Configure `.env`

```
VITE_API_URL=http://localhost:8000
```

### 3. Run frontend

```
npm run dev
```

App will run at:

```
http://localhost:5173
```

---

# 🚀 Deployment

### Backend (Render)

* Use **Python 3.10+**
* Add environment variables
* Add build command:

```
pip install -r backend/requirements.txt
```

* Start command:

```
uvicorn backend.src.main:app --host=0.0.0.0 --port=$PORT
```

### Frontend (Netlify / Vercel)

* Build command:

```
npm run build
```

* Set environment variable:

```
VITE_API_URL=https://your-backend-url.onrender.com
```

---

# 🧠 Key Features (Detailed)

### 🔍 **Email Categorization**

* LLM predicts exactly one label
* Uses DB-stored prompt for full control
* Falls back to heuristics (optional)

### 🧾 **Task Extraction**

* Returns list of structured tasks:

```json
[
  { "task": "Review the contract", "deadline": "2024-06-10" },
  { "task": "Send feedback", "deadline": null }
]
```

### 🤖 **Chat Agent**

* Context-aware responses
* Works with or without selected email
* Used by ChatBox UI

### 📝 **Draft Generator**

* Returns:

```json
{
  "subject": "Re: [Original Subject]",
  "body": "Here is your professional reply..."
}
```

* Saved in DB
* Viewed in Drafts list and DraftDetail page

### 🧩 **Prompt Editor**

* Live updates to prompts
* Stored in DB
* Used instantly by LLM service

---

# 🔌 API Overview

Common routes:

### `/inbox`

Fetch all emails (with tasks, category, drafts).

### `/inbox/load`

Load mock emails (safe for testing).

### `/email/{id}`

Get details of one email.

### `/agent/chat`

Context-aware chat with LLM.

### `/agent/draft`

Generate reply draft.

### `/draft/generate`

Generate and store a draft.

### `/drafts`

Get all drafts.

### `/prompts`

Get or update prompt templates.

### `/process/reprocess`

Recompute categories + tasks for all emails.

---

# 🧪 Development Tools

### Auto reload backend

```
uvicorn src.main:app --reload
```

### Pretty API logs

In `api.js` → Axios interceptors already added.

---

# ⚠️ Troubleshooting

### ❌ LLM not being used

Check:

```
/health → llm: "available"
```

### ❌ Tasks always empty

Check LLM logs:

```
llm_service._call() logs
safe_json_extract() output
```

### ❌ Inbox not processing

Call:

```
POST /process/reprocess
```

### ❌ Cors issues

Frontend URL must match:

```
allow_origins=["*"] or frontend URL
```

---

# 📄 License

MIT — free to use, modify, deploy.

---

# 🤝 Contributing

PRs welcome! You can improve:

* UI (shadcn components)
* New AI capabilities
* Attachments parsing
* Multi-account inbox sync

---

# 🙌 Credits

Built by **TailMind Team** — powered by Gemini LLM.
Backend (FastAPI), Frontend (React), DB (SQLModel/Postgres).
