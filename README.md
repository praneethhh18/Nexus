```
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
```

**A private AI business OS with a named team of autonomous agents —
runs local-first, stays local for anything sensitive, and uses the cloud
only for polished writing on aggregates you explicitly allow.**

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is NexusAgent?

NexusAgent is a private AI business OS for small teams. One app replaces the
patchwork of Notion AI + Zapier + an analytics dashboard + a CRM + an invoice
tool, with one crucial difference: **customer data never leaves your machine**[^voice],
while reports still get cloud-quality writing via a strict aggregate-only path.

[^voice]: Outbound voice calls are the one exception — Vox uses cloud
providers (Twilio, Groq, ElevenLabs) for audio routing, transcription, and
synthesis. Transcripts and summaries stay local. See the **Cloud providers ·
Voice agent** card on the Security page in-app for the full disclosure.

Under the hood it combines a local LLM (Ollama), a vector database (ChromaDB),
a SQL agent, a multi-agent orchestrator (LangGraph), a drag-and-drop workflow
builder, and a four-layer privacy gate on every outbound call — wired into a
React + FastAPI application.

You get a named team of seven agents (Atlas, Iris, Kira, Arjun, Sage, Nyx, Echo)
that run on their own schedules, surface proactive nudges, and can be renamed
to match your team's vocabulary. Everything the agents do is logged in a single
activity feed and gated behind human approval when it touches the outside world.

---

## Key Features

### Your AI team

- **Seven named agents with personas** — Atlas (Chief of staff · morning briefings), Iris (Inbox triage), Kira (Invoice chaser), Arjun (Pipeline watcher), Sage (Meeting prep), Nyx (Evening digest), Echo (Memory keeper · weekly). Rename any of them from the `/agents` page.
- **Morning briefing** — Atlas writes a 1-page summary of tasks, overdue items, and pipeline every day at 08:00 (aggregates only — never raw rows leaving the machine).
- **Proactive nudges** — agents raise a hand when they notice something: *"Kira noticed 2 overdue invoices — draft reminders?"* One click to accept, one click to dismiss for the day.
- **Run Now** — trigger any agent on demand from the `/agents` page. Each shows its own "last ran" timestamp and activity count.
- **Unified activity feed** — everything all seven agents did in the last 48 hours, newest first, stamped with the persona that did it.

### Work the product

- **Smart Inbox** (`/inbox`) — one page for "what needs me right now": pending approvals, proactive nudges, overdue tasks, today's meetings. Empty sections hide.
- **AI Chat with slash commands** — natural language or `/remind`, `/task`, `/deal`, `/contact`, `/invoice`, `/brief`, `/triage`. Type `/` for a typeahead menu; commands reuse the agent tool system.
- **Voice chat mode** — fullscreen hands-free conversation with an animated orb, VAD-based listening (no fixed 5-second cap), and spoken responses. Whisper STT + browser-native TTS. Nothing leaves your machine.
- **CRM + Tasks + Invoices** — Lead → Deal → Task → Invoice → Paid flow, with a banner showing where the current page fits.
- **Document templates** — generate proposals, SOWs, contracts, offer letters from templates.
- **Dashboard sample data** — one-click "Load sample data" on an empty workspace so you can see the product in action in 30 seconds.

### Privacy-first hybrid intelligence

- **4-layer privacy gate** — (1) `ALLOW_CLOUD_LLM` kill switch, (2) sensitivity routing that forces DB/email prompts to local Ollama, (3) PII redaction (emails, phones, Aadhaar/PAN/SSN, cards, secrets) before any cloud call, (4) audit log at `outputs/cloud_audit.jsonl` with SHA-256 fingerprints only — never raw prompts.
- **Aggregate-then-cloud reports** — row-level business data never leaves the machine. Totals, means, and top-5 category breakdowns are computed locally, redacted, and only then sent to the cloud for narrative writing. See `report_generator/narrative.py`.
- **Cloud Privacy panel** (`/security`) — live view of every cloud call: provider, model, redaction count, payload size, SHA fingerprint. Proof of safety, not a promise.
- **Developer mode** — a master toggle on Settings. Off by default: non-tech users see only the essentials. On: full LLM config, system info, IMAP triage, SQL editor, database explorer.

### Foundations

- **Natural Language SQL** — plain-English queries auto-generate SQL with self-correction; all execution stays on local SQLite.
- **Document Q&A** — PDFs/DOCX, multi-document comparison, cross-source reasoning; embeddings always local via `nomic-embed-text`.
- **Workflow automation** — drag-and-drop React Flow node builder, 10 pre-built templates.
- **PDF reports** — charts + tables + executive summaries from the aggregate-then-cloud path.
- **What-If simulator** — before/after impact analysis with CFO-style critique.
- **Human-in-the-loop** — any outbound action (emails, SMS, invoice sends) is drafted and queued for explicit approval in `/inbox`.
- **Full audit trail** — every tool call timestamped with inputs, outputs, approver.
- **2FA + session management** — TOTP enrollment, recovery codes, per-device session revocation.
- **Zero-subscription stack** — Ollama + SQLite + ChromaDB + FastAPI + React. Cloud LLM optional (Anthropic Claude or AWS Nova). Everything else free and open-source.

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

## Privacy Architecture — 360° Automation Without 360° Exposure

NexusAgent is built for end-to-end business automation, which means every
outbound communication, invoice, report, and email workflow touches real data:
customer names, revenue, emails, internal metrics. The moment you add a cloud
LLM to the stack for higher-quality reasoning, that data becomes at risk of
leaving the machine. **NexusAgent's privacy layer is the gate that prevents
this**, with zero impact on feature depth or latency.

### The four defenses (in order)

```
User chat ──► Intent detector ──► Agent node
                                      │
                                      ▼
                           ┌───────────────────────┐
                           │   1.  Kill switch     │   ALLOW_CLOUD_LLM=false
                           │        (if on)        │ → force all calls local
                           ├───────────────────────┤
                           │   2.  Sensitivity     │   sensitive=True flags
                           │        routing        │ → force local for DB/PII
                           ├───────────────────────┤
                           │   3.  Local           │   SQL, row explanation,
                           │        aggregation    │ → email triage stay here
                           ├───────────────────────┤
                           │   4.  PII redaction   │   emails, phones, IDs,
                           │        + audit log    │ → secrets → tokens
                           └───────────────────────┘
                                      │
                              Only then, if at all,
                              does the payload leave.
```

### What goes where

| Data type | Path | Why |
|---|---|---|
| **Raw DB rows** (customers, invoices, transactions) | Never leaves — local Ollama only | `sensitive=True` enforced in `sql_agent/executor.py` and `query_generator.py` |
| **Email bodies** (triage, classification) | Never leaves — local Ollama only | `sensitive=True` in `agents/email_triage.py` |
| **RAG embeddings** (your docs) | Always local | `config/llm_provider.get_embedder` locked to `nomic-embed-text` |
| **Aggregates** (totals, means, top-5) | Redacted, then cloud (optional) | `report_generator/narrative.py` computes locally first |
| **Chit-chat / generic reasoning** | Redacted, then cloud (optional) | Not business-specific, PII still stripped before send |

### Aggregate-then-cloud for reports — why it's the safest and best-quality approach

When you ask for a report, NexusAgent does not send your database to a cloud
LLM. The flow is:

1. **Local SQL** — the agent generates SQL against your schema using local
   Ollama (schema context stays on your machine) and executes on local SQLite.
2. **Local aggregation** — `report_generator/narrative.compute_aggregates`
   reduces the DataFrame to totals, means, min/max, and top-5 category
   breakdowns. Nothing row-level is kept.
3. **PII redaction** — category labels (which can contain customer/vendor
   names) are scrubbed via `config/privacy.redact` with a reversible map.
4. **Cloud narrative** — only the redacted aggregate dict goes to Nova Pro /
   Claude, which writes the executive prose. Because the payload is small,
   latency is low (~1-2s vs. 10s+ for a full-row prompt).
5. **Local restore** — the response is un-redacted locally before you see it.
6. **Audit log** — `outputs/cloud_audit.jsonl` records every cloud call with
   a SHA-256 of the (already-redacted) payload, never the raw content.

**Why this beats "all local" and "all cloud":**

- *All local (Ollama only):* safe but produces weaker prose on large tabular
  reports; the 8B model struggles with multi-paragraph reasoning.
- *All cloud (send rows to Nova):* high quality but leaks every record in the
  report payload to a third party.
- *Aggregate-then-cloud (this design):* cloud-quality narrative with an
  input 20-50× smaller → lower latency, lower cost, and zero row-level
  exposure. Your customers never appear in an outbound packet.

### Privacy controls (all in `.env`)

```bash
ALLOW_CLOUD_LLM=true      # master kill switch; false = Ollama only
REDACT_PII=true           # scrub emails/phones/IDs/secrets before cloud calls
AUDIT_CLOUD_CALLS=true    # log every cloud call to outputs/cloud_audit.jsonl
```

Verified by `tests/test_privacy.py` (9 tests). See `config/privacy.py` for the
redaction patterns and `report_generator/narrative.py` for the aggregation
pipeline.

---

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| Frontend | React + Vite + Tailwind CSS | Fast, modern, no full-page reruns |
| Workflow Canvas | React Flow (@xyflow/react) | Drag-and-drop node editor |
| Backend API | FastAPI + Uvicorn | Async, fast, auto-docs |
| LLM (local) | Ollama + llama3.1:8b | Private reasoning on raw business data |
| LLM (cloud, optional) | Claude Sonnet / Amazon Nova Pro | Polished narratives on *aggregates only* |
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

278 backend tests (privacy, multi-tenant isolation, persona-schedule contract, migration runner, backup, what-if tenant scope, and more) + 27 Playwright e2e scenarios.

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
├── tests/              278 backend tests + Playwright e2e suite
├── db/                 Migration runner + versioned schema files
├── data/               SQLite database + uploaded documents
├── outputs/            Generated PDFs, charts, email drafts, exports
├── chroma_db/          ChromaDB vector store
└── start.bat           One-click launcher (Windows)
```

---

## License

MIT License — free to use, modify, and distribute.

---

## Documentation

Long-form docs live in [`docs/`](./docs/):

- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — engineer-facing architecture & contributor guide
- **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** — install, configure, deploy
- **[docs/DEMO_PLAYBOOK.md](./docs/DEMO_PLAYBOOK.md)** — guided demo scripts
- **[docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)** — how to verify features
- **[docs/CHANGELOG.md](./docs/CHANGELOG.md)** — version history
- **[docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md)** — contribution rules
- **[docs/README.md](./docs/README.md)** — full docs index

---

*NexusAgent v2.0 — 100% local, zero API cost, production-grade AI business automation.*
