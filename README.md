```
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
```

**Multi-agent AI business assistant that reads your documents, queries your data, builds automations,
and monitors your business — all running 100% locally for free.**

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Tests](https://img.shields.io/badge/tests-72%20passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is NexusAgent?

NexusAgent is a production-grade AI business assistant that runs entirely on your local machine.
It combines a local LLM (via Ollama), a vector database (ChromaDB), a SQL agent, a multi-agent
orchestrator (LangGraph), and a drag-and-drop workflow automation builder into a modern
React frontend powered by a FastAPI backend.

Unlike cloud AI tools, NexusAgent keeps all your data local, runs at zero cost after setup,
and gives you full transparency through a complete audit trail. It learns from your conversations,
proactively monitors your business for anomalies, and can take real actions like sending
emails — always with your explicit approval first.

---

## Key Features

- **AI Chat** — Ask business questions in natural language; get answers with citations and charts
- **Natural Language SQL** — Query your database in plain English; auto-generates SQL with self-correction
- **Document Q&A** — Upload PDFs/DOCX and ask questions; multi-document comparison and cross-source reasoning
- **Workflow Automation** — Drag-and-drop node builder (React Flow) with 10 pre-built templates
- **PDF Report Generation** — Professional reports with charts, tables, and executive summaries
- **What-If Simulator** — Model business scenarios with before/after impact analysis and CFO critique
- **Proactive Anomaly Detection** — Background monitoring alerts you when data looks abnormal
- **Database Explorer** — Browse tables, view schemas, preview data, import CSV/Excel
- **Conversation Persistence** — Chat sessions saved and loadable from sidebar
- **Query History** — Searchable history with star, re-run, and filter
- **Export** — Download conversations as Markdown or PDF
- **Human-in-the-Loop Actions** — Emails drafted and shown for approval before sending
- **Self-Reflection Loop** — Agent reviews its own answers before showing them to you
- **Voice Input/Output** — Speak queries (Whisper STT) and hear responses (pyttsx3 TTS)
- **Full Audit Trail** — Every tool call logged with timestamps, inputs, outputs
- **Multi-Agent Collaboration** — Complex queries decomposed across specialist agents
- **10 Workflow Templates** — Daily reports, anomaly alerts, email sender, meeting scheduler, churn detection, and more
- **Zero API Cost** — 100% local, 100% open source, $0 after setup

---

## Architecture

```
React Frontend (Vite + Tailwind + React Flow)
        │
        │  REST API + WebSocket
        ▼
FastAPI Server (api/server.py)
        │
        ├─── Orchestrator (LangGraph)
        │       ├── Tone Analyzer
        │       ├── Intent Detector
        │       ├── RAG Node (ChromaDB)
        │       ├── SQL Node (SQLite)
        │       ├── Action Node (Email/Discord)
        │       ├── Report Node (ReportLab + Plotly)
        │       ├── What-If Node
        │       ├── Multi-Agent Node
        │       ├── Synthesizer
        │       └── Self-Reflection
        │
        ├─── Workflow Engine
        │       ├── Node Registry (20+ node types)
        │       ├── Executor (topological sort + branching)
        │       ├── Scheduler (APScheduler)
        │       └── Templates (10 pre-built automations)
        │
        ├─── Memory
        │       ├── Conversation Store (SQLite)
        │       ├── Query History (SQLite)
        │       ├── User Memory & Patterns
        │       ├── Short-Term (RAM)
        │       ├── Long-Term (SQLite)
        │       └── Audit Logger
        │
        └─── Voice
                ├── STT (faster-whisper)
                └── TTS (pyttsx3)
```

---

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| Frontend | React + Vite + Tailwind CSS | Fast, modern, no full-page reruns |
| Workflow Canvas | React Flow (@xyflow/react) | Drag-and-drop node editor |
| Backend API | FastAPI + Uvicorn | Async, fast, auto-docs |
| LLM | Ollama + llama3.1:8b | Local, free, powerful |
| Embeddings | Ollama + nomic-embed-text | Local, no API needed |
| Vector DB | ChromaDB | Local, persistent |
| Orchestrator | LangGraph | Production-grade agent graph |
| Database | SQLite | Local, zero config |
| PDF parsing | PyMuPDF | Best open source parser |
| Voice input | faster-whisper | Local Whisper STT |
| Voice output | pyttsx3 | Fully offline TTS |
| Charts | Plotly | Interactive visualizations |
| PDF reports | ReportLab | Professional PDF output |
| Scheduling | APScheduler | Background job runner |

---

## Prerequisites

- **Python 3.11+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **Ollama** — [ollama.ai](https://ollama.ai)
- 8GB+ RAM recommended (for 8B parameter model)

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-org/nexusagent.git
cd nexusagent

# 2. Backend setup
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

# 3. Frontend setup
cd frontend
npm install
cd ..

# 4. Pull Ollama models
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull nomic-embed-text

# 5. Configure environment
cp .env.example .env
# Edit .env with your settings (defaults work out of the box)
```

---

## Running the App

### One-Click Launch (Windows)

Double-click **`start.bat`** — starts Ollama + API + Frontend + opens browser.

### Manual Launch

**Terminal 1 — API Server:**
```bash
cd nexusagent
venv\Scripts\activate
uvicorn api.server:app --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd nexusagent/frontend
npm run dev
```

Open **http://localhost:5173**

API docs at **http://localhost:8000/docs**

On first launch:
- SQLite database auto-created with sample business data (8 tables)
- 4 sample business documents auto-loaded into RAG knowledge base
- Proactive anomaly monitoring starts in background

---

## Pages

| Page | What it does |
|---|---|
| **Chat** | AI chat with tool badges, source citations, quick actions, export |
| **Database** | Table browser, schema viewer, data preview, CSV/Excel import |
| **What-If** | Scenario simulator with before/after metrics and CFO critique |
| **Reports** | Generate and download PDF business reports |
| **Workflows** | Drag-and-drop automation builder with React Flow canvas |
| **History** | Searchable query history with star, re-run, and filters |
| **Settings** | Model config, system info, available Ollama models, maintenance |

---

## Workflow Automation

The workflow builder lets you create n8n-style automations by connecting nodes:

### Node Categories (20+ types)
- **Triggers** — Schedule (cron/daily/weekly), Manual, Anomaly Detected, Webhook
- **Data** — SQL Query, Document Search (RAG), Web Search, Data Transform
- **AI** — LLM Prompt, Summarize, Generate PDF Report, AI Classify
- **Conditions** — Value Check, AI Decision, Data Exists
- **Actions** — Send Email, Discord/Desktop Notify, HTTP Request, Save File
- **Control** — Wait/Delay, Merge

### Pre-Built Templates (10)
1. **Daily Sales Report** — morning query + summarize + PDF + save
2. **Anomaly Alert Pipeline** — hourly check + AI decision + Discord alert
3. **Weekly KPI Digest** — pull KPIs + draft summary + PDF + email team
4. **Document Monitor** — daily RAG search + summarize + save + notify
5. **Revenue Drop Response** — compare revenue + AI recovery plan + alert
6. **Auto Email Sender** — gather data + AI drafts email + send
7. **Meeting Scheduler** — pull data + generate agenda + email invite
8. **Call Scheduler & Prep** — client data + doc search + talking points + email
9. **Live Data Fetcher** — web search + AI analysis + classify urgency + store/alert
10. **Customer Churn Warning** — find at-risk + AI analysis + email sales team

---

## API Endpoints

The FastAPI server exposes 30+ REST endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | System health + Ollama status |
| `/api/chat` | POST | Send a chat message |
| `/ws/chat` | WS | WebSocket for streaming chat |
| `/api/conversations` | GET/POST | List/create conversations |
| `/api/conversations/{id}` | GET/PATCH/DELETE | Manage a conversation |
| `/api/database/tables` | GET | List all database tables |
| `/api/database/tables/{name}` | GET | Table schema + data preview |
| `/api/database/import` | POST | Import CSV/Excel as new table |
| `/api/reports/generate` | POST | Generate a PDF report |
| `/api/reports` | GET | List recent reports |
| `/api/whatif` | POST | Run what-if simulation |
| `/api/history` | GET/DELETE | Query history with search/filter |
| `/api/workflows` | GET/POST | List/save workflows |
| `/api/workflows/{id}/run` | POST | Execute a workflow |
| `/api/workflows/templates` | GET | Get pre-built templates |
| `/api/workflows/node-types` | GET | Get all available node types |
| `/api/knowledge` | GET | Knowledge base sources |
| `/api/knowledge/upload` | POST | Upload documents to RAG |
| `/api/monitor/run` | POST | Run anomaly check |
| `/api/settings` | GET | System configuration |

Full interactive docs at **http://localhost:8000/docs**

---

## Configuration

Edit `.env` — minimum required:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
EMBED_MODEL=nomic-embed-text:latest
```

Optional:
```bash
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## Running Tests

```bash
# Core unit tests (no Ollama required)
python -m pytest tests/test_core.py tests/test_new_features.py -v

# Full E2E tests (requires Ollama running)
python tests/test_e2e.py
```

72 unit tests + 6 E2E scenarios.

---

## Project Structure

```
nexusagent/
├── api/                FastAPI server + WebSocket endpoints
├── frontend/           React + Vite + Tailwind + React Flow
│   └── src/
│       ├── pages/      Chat, Database, WhatIf, Reports, Workflows, History, Settings
│       ├── components/ Layout shell with sidebar
│       └── services/   API client layer
├── config/             LLM connection, settings, .env loader
├── orchestrator/       LangGraph graph, nodes, intent detector, self-reflection
├── sql_agent/          NL-to-SQL, schema reader, executor, data import
├── rag/                Ingestion, embeddings, ChromaDB, multi-document retrieval
├── action_tools/       Email, Discord/desktop notifications, file dispatcher
├── report_generator/   Chart selection, Plotly builder, ReportLab PDF
├── voice/              Whisper STT, pyttsx3 TTS, tone analyzer
├── memory/             Conversations, query history, user memory, audit logger
├── workflows/          Node registry, executor, scheduler, templates, storage
│   └── nodes/          Trigger, condition, data, AI, and action node runners
├── utils/              What-if simulator, export, sample doc generator
├── tests/              72 unit tests + E2E suite
├── data/               SQLite database + uploaded documents
├── outputs/            Generated PDFs, charts, email drafts, exports
├── chroma_db/          ChromaDB vector store
└── start.bat           One-click launcher (Windows)
```

---

## License

MIT License — free to use, modify, and distribute.

---

*NexusAgent v2.0 — 100% local, zero API cost, production-grade AI business automation.*
