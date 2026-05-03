```
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
```

**A private AI business OS with a named team of eight autonomous agents —
runs local-first for everything sensitive, uses the cloud only on aggregates
you explicitly allow, and now ships a CRM-integrated outbound voice agent.**

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is NexusAgent?

NexusAgent is a private AI business OS for small teams. One app replaces the
patchwork of Notion AI + Zapier + an analytics dashboard + a CRM + an invoice
tool, with one crucial difference: **for non-voice features, customer data
never leaves your machine** — local LLM, local SQL, local embeddings.
Reports use a strict aggregate-only path when you opt into a cloud LLM.

**Outbound voice calls are the single explicit exception.** When you click
**"Call with Vox"** on a contact, the dial happens in a sister project
(**[NexusCaller-lab](https://github.com/praneethhh18/NexusCaller-lab)**)
which uses Twilio (PSTN), LiveKit (audio + Krisp echo cancellation), Groq
(STT + LLM), and ElevenLabs / Cartesia (TTS). Transcripts and summaries
come back into NexusAgent's local DB. The /security page lists every cloud
provider in use. We don't pretend voice is local — it isn't.

---

## The team — 8 named agents

| Agent | Default name | Role | Schedule |
|---|---|---|---|
| `morning_briefing` | **Atlas** | Chief of staff · 1-page morning briefing | Daily 08:00 |
| `email_triage` | **Iris** | Inbox triage + reply drafts | Every 15 min |
| `invoice_reminder` | **Kira** | Spots overdue invoices, drafts reminders for approval | Daily 09:00 |
| `stale_deal_watcher` | **Arjun** | Flags deals that haven't moved in 2+ weeks | Daily 08:30 |
| `meeting_prep` | **Sage** | Pre-meeting brief on contact + open deals | Every 10 min |
| `outbound_caller` | **Vox** | Calls CRM contacts on demand (audio runs in NexusCaller-lab) | Operator-triggered (heartbeat at 00:05) |
| `evening_digest` | **Nyx** | End-of-day recap of tasks/invoices/deals | Daily 18:00 |
| `memory_consolidate` | **Echo** | Weekly review + memory distillation | Weekly Sun 03:00 |

Rename any agent on the `/agents` page — they keep their role and
behaviour, just wear the new name.

---

## Key features

### Your AI team

- **Eight named agents** with personas, schedules, and per-agent activity
  logs. Triggered automatically on schedule, manually via "Run Now" on the
  `/agents` page, or proactively via nudges in `/inbox`.
- **Vox · outbound calling** — click ☎ on any CRM contact, pick a
  STT/LLM/TTS combo on the lab's precall page, watch the call live in the
  cockpit, see the structured summary land back on the contact record.
- **Unified activity feed** — what every agent did in the last 48h,
  newest first, stamped with the persona that did it.
- **Run-Now button** on every agent card. Each shows its own "last ran"
  timestamp + 24h activity count.

### Work the product

- **Smart Inbox** (`/inbox`) — pending approvals, proactive nudges,
  overdue tasks, today's meetings. Empty sections hide.
- **AI Chat with slash commands** — natural language or `/remind`, `/task`,
  `/deal`, `/contact`, `/invoice`, `/brief`, `/triage`. Type `/` for a
  typeahead menu; commands reuse the agent tool system. **Hard 90s
  timeout** so the UI doesn't hang on Thinking forever if Ollama stalls.
- **In-app voice chat** — fullscreen hands-free conversation with an
  animated orb. Audio captured by the browser, sent to a local Whisper
  STT endpoint, response spoken via the browser's native
  `speechSynthesis`. **Stays local.** Distinct from Vox outbound (which
  is the cloud-routed phone-call path).
- **CRM + Tasks + Invoices** — Lead → Deal → Task → Invoice → Paid flow.
- **Document templates** — proposals, SOWs, contracts, offer letters.
- **Sample data loader** — one-click on an empty workspace.

### Privacy gate (4 layers)

- **Kill switch** — `ALLOW_CLOUD_LLM=false` forces all calls to local Ollama.
- **Sensitivity routing** — DB / email prompts always go local regardless
  of the kill switch.
- **PII redaction** — emails, phones, Aadhaar/PAN/SSN, cards, secrets
  scrubbed via reversible token map before any cloud call.
- **Audit log** at `outputs/cloud_audit.jsonl` with SHA-256 fingerprints
  only, never raw prompts. Live view at `/security`.

### Foundations

- **Natural Language SQL** — plain English → SQL with self-correction;
  execution stays on local SQLite/Postgres.
- **Document Q&A** — PDFs / DOCX, multi-document comparison;
  embeddings always local via `nomic-embed-text`.
- **Workflow automation** — drag-and-drop React Flow canvas, 10 pre-built
  templates, 20+ node types.
- **PDF reports** — charts + tables + executive summaries from the
  aggregate-then-cloud path.
- **What-If simulator** — before/after impact analysis, multi-tenant
  scoped.
- **Human-in-the-loop** — every outbound action (emails, SMS, invoice
  sends) drafted and queued for explicit approval in `/inbox`.
- **Full audit trail** — every tool call timestamped with inputs,
  outputs, approver.
- **2FA + session management** — TOTP, recovery codes, per-device session
  revocation.

---

## Architecture

```
React Frontend (Vite + Tailwind + React Flow)
        │
        │  REST + WebSocket
        ▼
FastAPI Server (api/server.py)
        │
        ├── Orchestrator (LangGraph)
        │     ├── Tone analyzer · Intent detector · Synthesizer · Self-reflection
        │     ├── RAG node (ChromaDB)
        │     ├── SQL node (SQLite / Postgres)
        │     ├── Action node (Email / Discord / Notify)
        │     ├── Report node (ReportLab + Plotly, aggregate-then-cloud)
        │     └── What-If node + Multi-Agent node
        │
        ├── Workflow Engine
        │     ├── Node Registry (20+ node types)
        │     ├── Executor (topological sort + branching)
        │     ├── APScheduler (8 agent jobs + custom jobs)
        │     └── 10 pre-built templates
        │
        ├── Memory
        │     ├── Conversation Store · Query History · User Memory
        │     ├── Audit Logger (cloud_audit.jsonl)
        │     └── Run Log (per-agent run history)
        │
        ├── Voice (in-app)         ── voice/listener.py + voice/speaker.py
        │     └── Browser-mic → Whisper STT → orchestrator → browser TTS
        │
        └── Voice (Vox · outbound) ── api/routers/voice_calls.py
              POST /api/voice/prepare-dial
                  ↓
              opens NexusCaller-lab's precall page (separate repo)
                  ↓
              call audio + transcript + summary all happen in lab
                  ↓
              POST /api/voice/callback ← lab posts results back
                  ↓
              nexus_voice_calls table + nexus_interactions row +
              denormalized last_call_* on contact
```

---

## Privacy architecture

### Four defenses (in order)

```
User chat ──► Intent detector ──► Agent node
                                       │
                                       ▼
                            ┌───────────────────────┐
                            │  1. Kill switch       │   ALLOW_CLOUD_LLM=false
                            ├───────────────────────┤
                            │  2. Sensitivity       │   sensitive=True ⇒ local
                            ├───────────────────────┤
                            │  3. Local             │   SQL, row explanation,
                            │     aggregation       │     email triage stay here
                            ├───────────────────────┤
                            │  4. PII redaction     │   emails, phones, IDs
                            │     + audit log       │   secrets → tokens
                            └───────────────────────┘
```

### What goes where

| Data type | Path | Why |
|---|---|---|
| Raw DB rows (customers, invoices) | Always local | `sensitive=True` in SQL agent |
| Email bodies (triage) | Always local | `sensitive=True` in `email_triage.py` |
| RAG embeddings | Always local | `nomic-embed-text` via Ollama |
| Aggregates (totals, top-5) | Redacted → cloud (optional) | `report_generator/narrative.py` |
| Chit-chat / generic reasoning | Redacted → cloud (optional) | Not business-specific; PII still stripped |
| **Outbound call audio** | **Cloud (Twilio + LiveKit + Groq + ElevenLabs/Cartesia)** | Real-time voice can't be local on a laptop. See `/security` page for live disclosure. |

### Privacy controls (all in `.env`)

```bash
ALLOW_CLOUD_LLM=true      # master kill switch; false = local Ollama only
REDACT_PII=true           # scrub emails/phones/IDs/secrets before cloud calls
AUDIT_CLOUD_CALLS=true    # log every cloud call to outputs/cloud_audit.jsonl
```

Verified by `tests/test_privacy.py`. See `config/privacy.py` for the
redaction patterns and `report_generator/narrative.py` for the aggregation
pipeline.

---

## Tech stack

| Component | Tool | Why |
|---|---|---|
| Frontend | React + Vite + Tailwind | Fast, modern |
| Workflow canvas | React Flow | Drag-and-drop node editor |
| Backend API | FastAPI + Uvicorn | Async, fast, auto-docs |
| LLM (local) | Ollama + llama3.1:8b | Private reasoning on raw data |
| LLM (cloud, optional) | Anthropic Claude / Amazon Nova Pro | Polished narratives on aggregates only |
| Embeddings | Ollama + nomic-embed-text | Local |
| Vector DB | ChromaDB | Local, persistent |
| Orchestrator | LangGraph | Multi-node agent graph |
| Database | SQLite (default) or Postgres (`DATABASE_URL`) | Local, zero-config |
| PDF parsing | PyMuPDF | |
| In-app STT | faster-whisper | Local Whisper |
| In-app TTS | browser `speechSynthesis` | Local, no API |
| **Vox outbound voice** | **Twilio + LiveKit + Groq + ElevenLabs/Cartesia** | **Sister repo, see [NexusCaller-lab](https://github.com/praneethhh18/NexusCaller-lab)** |
| Charts | Plotly | |
| PDF reports | ReportLab | |
| Scheduling | APScheduler | |

---

## Prerequisites

- **Python 3.11+** (CI tests run on 3.12 and 3.13)
- **Node.js 18+**
- **Ollama** ([ollama.ai](https://ollama.ai))
- **Postgres** (optional — defaults to SQLite if `DATABASE_URL` is unset)
- 8 GB+ RAM recommended for the 8B model

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/praneethhh18/Nexus.git
cd Nexus

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
# Edit .env with your settings (defaults work for local-only dev)
```

To use **Vox outbound calling**, also clone and set up the sibling repo:
[NexusCaller-lab](https://github.com/praneethhh18/NexusCaller-lab). Its
README has the LiveKit + Twilio SIP trunk walkthrough.

---

## Running the app

### One-click (Windows)

Double-click **`start.bat`** — starts Ollama, the API on port 8000, and
the frontend on port 5173. Browser opens to `http://localhost:5173`.

### Manual

```bash
# Terminal 1 — API
venv\Scripts\activate
uvicorn api.server:app --port 8000 --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

API docs at **http://localhost:8000/docs**.

For Vox outbound calling, run **NexusCaller-lab**'s `start_all.bat` —
that boots NexusAgent + frontend + the lab's agent worker + lab server +
ngrok in one shot.

---

## Pages

| Page | What it does |
|---|---|
| **Dashboard** (`/`) | Today's briefing, pipeline snapshot, sample-data loader |
| **Inbox** (`/inbox`) | Approvals + proactive nudges + overdue tasks + today's meetings |
| **Chat** (`/chat`) | AI chat with tool badges, citations, slash commands. 90s timeout. |
| **CRM** (`/crm`) | Companies, contacts, deals, pipeline view |
| **Contact detail** (`/crm/contacts/:id`) | Profile + interactions + open deals + invoices + **Vox calls history** |
| **Tasks** (`/tasks`) | Kanban + due-today bucket |
| **Invoices** (`/invoices`) | Draft → sent → paid pipeline |
| **Documents** (`/documents`) | Templates + uploaded files for RAG |
| **Workflows** (`/workflows`) | Drag-and-drop automation canvas |
| **Reports** (`/reports`) | Generate / download PDF reports |
| **What-If** (`/whatif`) | Scenario simulator with CFO critique |
| **Database** (`/database`) | Schema browser + CSV import |
| **Agents** (`/agents`) | The 8 agent cards + activity feed |
| **Security** (`/security`) | Privacy gate status + cloud-provider disclosure (incl. voice) |
| **Settings** (`/settings`) | Model config, system info, sample-data, dev mode |

---

## Workflow automation

Drag-and-drop builder with 20+ node types: Triggers (Schedule, Manual,
Anomaly, Webhook), Data (SQL, RAG, Web, Transform), AI (LLM, Summarize,
Generate PDF, Classify), Conditions, Actions (Email, Discord, HTTP, File),
Control (Wait, Merge).

Ten pre-built templates covering daily sales reports, anomaly alerts,
weekly KPI digest, document monitor, revenue-drop response, auto-email
sender, meeting scheduler, call scheduler, live data fetcher, customer
churn warning.

---

## API endpoints

The FastAPI server exposes 50+ REST endpoints across 30+ routers. Highlights:

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | System health + Ollama status |
| `/api/chat` | POST | Send a chat message (90s timeout) |
| `/api/conversations` | GET / POST | List / create conversations |
| `/api/database/tables` | GET | List DB tables |
| `/api/reports/generate` | POST | Generate a PDF report |
| `/api/whatif` | POST | Run a what-if simulation |
| `/api/workflows` | GET / POST | List / save workflows |
| `/api/workflows/{id}/run` | POST | Execute a workflow |
| `/api/agents/personas` | GET | All 8 personas with last-run + 24h stats |
| `/api/agents/{key}/run` | POST | Trigger an agent on demand |
| `/api/voice/prepare-dial` | POST | Build precall URL for Vox + open it |
| `/api/voice/callback` | POST | Lab posts call results here (signed) |
| `/api/voice/calls` | GET | Recent Vox calls for the business |
| `/api/voice/contacts/{id}/calls` | GET | One contact's call history |
| `/api/voice/transcribe` | POST | In-app voice mode (browser mic → Whisper) |

Full interactive docs at **http://localhost:8000/docs**.

---

## Configuration

Minimum required in `.env`:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
EMBED_MODEL=nomic-embed-text:latest
```

Optional integrations:

```bash
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Postgres (default = SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/nexusagent

# Vox outbound calling (sister repo handles the audio path)
LAB_URL=http://localhost:8765
NEXUS_PUBLIC_URL=http://localhost:8000
VOICE_CALLBACK_SECRET=                # shared with NexusCaller-lab

# Cloud LLM for aggregate-only narratives (optional)
ANTHROPIC_API_KEY=
AWS_ACCESS_KEY_ID=                    # for Amazon Nova Pro
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
```

Full list with comments in `.env.example`.

---

## Tests

```bash
# Full backend suite
python -m pytest -q

# Just privacy / security
python -m pytest tests/test_privacy.py tests/test_persona_schedule_contract.py -q
```

**408 backend tests** + Playwright e2e suite. CI runs on Python 3.12 and
3.13. Privacy, multi-tenant isolation, persona-schedule contract,
migration runner, and what-if tenant scope are all covered.

The persona-schedule contract is strict: every agent declared in
`agents/personas.py::DEFAULTS` must have an entry in `SCHEDULER_JOB_IDS`,
a `_register("agent-...", ...)` call in `start_agent_scheduler`, and a
slot in `list_personas` order. Skip any of those = red CI.

---

## Project structure

```
Nexus/
├── api/                FastAPI server, 30+ routers (CRM, voice, workflows, …)
├── agents/             Atlas/Iris/Kira/Arjun/Sage/Nyx/Echo/Vox personas, run_log,
│                       background scheduler, tool registry, briefing, summarizer
├── frontend/           React + Vite + Tailwind + React Flow
│   └── src/pages/      Chat, CRM, ContactDetail (Vox calls panel), Agents,
│                       Workflows, Reports, Security, …
├── orchestrator/       LangGraph graph + nodes (intent, RAG, SQL, action, report)
├── sql_agent/          NL→SQL with self-correction
├── rag/                ChromaDB ingestion + retrieval
├── action_tools/       Email + Discord + desktop notify
├── report_generator/   Aggregate-then-cloud narrative + PDF (ReportLab + Plotly)
├── voice/              In-app voice mode (browser mic → Whisper STT)
├── memory/             Conversations, query history, user memory, audit log
├── workflows/          Node registry + executor + 10 templates
├── config/             LLM provider, privacy gate, settings, DB
├── db/                 Migration runner + versioned schemas
├── tests/              408 backend tests + Playwright e2e
├── outputs/            Generated PDFs / charts / transcripts (gitignored)
├── chroma_db/          ChromaDB vector store (gitignored)
└── start.bat           One-click launcher
```

---

## Companion repository

**[NexusCaller-lab](https://github.com/praneethhh18/NexusCaller-lab)** —
the voice-calling half. Owns the LiveKit Agent worker, Twilio SIP trunk
integration, the precall combo picker, and the live cockpit. Talks to
this repo over HTTP via the env var `LAB_URL`.

If you don't need outbound calling, you can ignore the sister repo and
NexusAgent runs fine on its own.

---

## License

MIT — free to use, modify, and distribute.

---

## Documentation

Long-form docs live in [`docs/`](./docs/):

- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — engineer-facing architecture
- [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) — install + configure + deploy
- [`docs/DEMO_PLAYBOOK.md`](./docs/DEMO_PLAYBOOK.md) — guided demo scripts
- [`docs/TESTING_GUIDE.md`](./docs/TESTING_GUIDE.md) — verifying features
- [`docs/CHANGELOG.md`](./docs/CHANGELOG.md) — version history
