# 🛡️ Ultron Mark II — Timekeeper

> **Prototype** · An AI-powered academic calendar management system

Ultron Mark II is a single-user web application that turns a Google Calendar into a dynamic, AI-driven study planner. It combines a conversational LLM interface with intelligent scheduling algorithms to help students manage coursework, resolve conflicts, and optimize study time.

> [!NOTE]
> This is a **prototype / proof-of-concept** and is not intended for production use. Expect rough edges, experimental features, and ongoing development.

---

## ✨ Features

| Feature | Description |
|---|---|
| **AI Chat Assistant** | Conversational interface powered by OpenAI with function-calling to manage your schedule through natural language |
| **Smart Scheduling** | Automatic study block placement that respects wake/sleep times, commute, dinner, and existing commitments |
| **Google Calendar Sync** | Two-way integration — reads existing events, writes study blocks, and detects conflicts |
| **Hybrid Memory** | SQL for short-term conversation context + ChromaDB vector store for long-term knowledge retrieval |
| **Task Management** | Create, prioritize, and track academic tasks with deadlines and course tags |
| **Conflict Detection** | Automatically identifies scheduling overlaps and suggests resolutions |
| **Real-Time Streaming** | Server-sent streaming responses for a responsive chat experience |
| **Daily Overrides** | Temporary schedule adjustments (e.g., skip commute, custom departure time) |
| **File Uploads** | Attach documents to chat conversations for context-aware assistance |

---

## 🏗️ Architecture

```
Ultron_P_MKII/
├── backend/                 # Python FastAPI server
│   ├── main.py              # App entry point, CORS, router registration
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── crud.py              # Database CRUD operations
│   ├── database.py          # SQLite engine & session config
│   ├── routers/
│   │   ├── auth.py          # Google OAuth flow
│   │   ├── chat.py          # Chat endpoints (sync + streaming)
│   │   ├── preferences.py   # User preferences CRUD
│   │   ├── schedule.py      # Scheduling & calendar endpoints
│   │   └── tasks.py         # Task management endpoints
│   ├── services/
│   │   ├── llm.py           # OpenAI integration & function-calling tools
│   │   ├── scheduler.py     # Study block placement algorithm
│   │   ├── memory.py        # Hybrid memory (SQL + ChromaDB)
│   │   └── calendar_integration.py  # Google Calendar API wrapper
│   └── requirements.txt
└── frontend/                # Next.js (React) web client
    ├── app/
    │   ├── page.tsx          # Dashboard — calendar view & conflicts
    │   ├── chat/             # AI chat interface
    │   ├── tasks/            # Task management page
    │   └── settings/         # Preferences & Google auth
    ├── components/
    │   └── Navbar.tsx        # Navigation bar
    └── lib/
        └── api.ts            # Backend API client
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, TypeScript |
| **Backend** | Python, FastAPI, Uvicorn |
| **Database** | SQLite (via SQLAlchemy ORM) |
| **Vector Store** | ChromaDB (long-term memory) |
| **AI** | OpenAI API (GPT with function calling) |
| **Calendar** | Google Calendar API (OAuth 2.0) |
| **Streaming** | FastAPI `StreamingResponse` + `ReadableStream` |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **OpenAI API key**
- **Google Cloud project** with Calendar API enabled and OAuth 2.0 credentials

### 1. Clone the Repository

```bash
git clone https://github.com/spedatox/ultron-mark-2.git
cd Ultron_P_MKII
```

### 2. Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
# Windows
.\venv\Scripts\Activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Configure Google OAuth credentials
cp credentials.example.json credentials.json
# Edit credentials.json with your Google Cloud OAuth client ID & secret

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The UI will be available at `http://localhost:3000`.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for the chat assistant | ✅ |

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Google Calendar API**
3. Create **OAuth 2.0 Client ID** credentials (Web application)
4. Add `http://localhost:8000/auth/google/callback` as an authorized redirect URI
5. Download the credentials JSON and save it as `backend/credentials.json`

---

## 📸 Screenshots

*Coming soon — this is an active prototype.*

---

## ⚠️ Disclaimer

This project is a **prototype (Mark II)**. It is built for personal use and learning purposes. It is not production-ready and may contain bugs, incomplete features, or security considerations that have not been fully addressed.

---

## 📄 License

This project is provided as-is for educational and prototyping purposes.
