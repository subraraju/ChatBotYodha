# ChatBot Yodha v2

A full-stack customer-service chatbot with meeting scheduling.

## Architecture

```
upgrade_chatbot_yodha/
├── .env.example            # All environment variables
├── .gitignore
├── docker-compose.yml      # Postgres + Backend + Frontend
├── sql/
│   ├── 01_create_tables.sql
│   └── 02_seed_data.sql
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml       # pytest config
│   ├── alembic.ini
│   ├── alembic/             # DB migration scripts
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Settings from .env
│   │   ├── database.py      # SQLAlchemy engine + session
│   │   ├── models.py        # ORM: Customer, Product, Sales, Activity
│   │   ├── schemas.py       # Pydantic DTOs
│   │   ├── logging_config.py
│   │   ├── chatbot/
│   │   │   └── __init__.py  # State-machine chatbot engine
│   │   ├── api/
│   │   │   ├── chat.py      # REST + WebSocket /chat endpoints
│   │   │   ├── customers.py # Read-only /data CRUD
│   │   │   └── admin.py     # Config + PDF upload
│   │   └── services/
│   │       ├── llm_service.py       # OpenAI / Ollama
│   │       ├── customer_lookup.py   # DB queries
│   │       ├── embedding_service.py # FAISS + SentenceTransformers
│   │       ├── calendar_service.py  # Google Calendar
│   │       ├── notification_service.py # Email, WhatsApp, Telegram
│   │       ├── storage_service.py   # Azure Blob / local
│   │       └── activity_service.py  # Activity table CRUD
│   └── tests/
│       ├── conftest.py
│       ├── test_customer_lookup.py
│       ├── test_chatbot.py
│       └── test_api.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts
│       ├── types.ts
│       ├── index.css
│       └── components/
│           ├── ChatWindow.tsx
│           ├── MessageBubble.tsx
│           ├── Sidebar.tsx
│           └── AdminPanel.tsx
└── data/                    # Runtime data (gitignored)
    ├── index/               # FAISS vector store
    ├── docs/                # Uploaded product PDFs
    └── chat_sessions/       # Local conversation exports
```

## Two Flows

### 1. Customer Service Chat
1. Customer provides email/phone → looked up in DB
2. Recent purchases displayed (paginated, 5 per page)
3. Select a product → ask questions → answered via FAISS vector search over product PDFs
4. On session close → conversation saved to Azure Blob, activity recorded, email summary sent

### 2. Marketing Meeting Scheduling
1. Customer says "schedule a meeting" / "book a call"
2. Shown list of marketing persons (party_type=MKTG in customer table)
3. Pick a person → calendar slots fetched from Google Calendar
4. Book a slot → Google Calendar event created, notifications sent

## Quick Start

### Option A: Docker Compose (recommended)

```bash
# 1. Copy and fill environment variables
cp .env.example .env

# 2. Start everything
docker compose up --build

# 3. Open
#    Frontend:  http://localhost:5173
#    Backend:   http://localhost:8000/docs
#    pgAdmin:   http://localhost:5050
```

### Option B: Local Development

**Backend:**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Set DATABASE_URL (or run Postgres via docker compose up postgres)
set DATABASE_URL=postgresql://chatbot:chatbot123@localhost:5432/chatbot_yodha

uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Seed the database:**

```bash
# If using Docker Compose, SQL scripts run automatically on first start.
# Otherwise, run manually:
psql -h localhost -U chatbot -d chatbot_yodha -f sql/01_create_tables.sql
psql -h localhost -U chatbot -d chatbot_yodha -f sql/02_seed_data.sql
```

## Database Migrations (Alembic)

```bash
cd backend

# Generate a new migration after modifying models.py
alembic revision --autogenerate -m "describe change"

# Apply migrations
alembic upgrade head
```

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Key Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `LLM_PROVIDER` | No | `openai` | `openai` or `ollama` |
| `OPENAI_API_KEY` | If openai | — | OpenAI API key |
| `OLLAMA_BASE_URL` | If ollama | `http://localhost:11434` | Ollama server URL |
| `SMTP_SERVER` | No | — | SMTP host for email notifications |
| `TWILIO_ACCOUNT_SID` | No | — | Twilio for WhatsApp |
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram bot token |
| `GOOGLE_CALENDAR_CREDENTIALS_FILE` | No | — | Path to Google Calendar OAuth JSON |
| `AZURE_STORAGE_CONNECTION_STRING` | No | — | Azure Blob for conversation export |

See `.env.example` for the full list.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat/start` | Start new chat session |
| `POST` | `/chat/{id}/message` | Send a message |
| `GET` | `/chat/{id}` | Get session info |
| `POST` | `/chat/{id}/close` | Close session |
| `WS` | `/chat/ws/{id}` | WebSocket chat |
| `GET` | `/data/customers` | List customers |
| `GET` | `/data/products` | List products |
| `GET` | `/data/sales` | List sales |
| `GET` | `/data/marketing-persons` | List marketing persons |
| `GET` | `/admin/config` | App configuration |
| `POST` | `/admin/upload-docs` | Upload PDFs for indexing |
