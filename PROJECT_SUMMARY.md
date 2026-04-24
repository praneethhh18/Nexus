# NexusAgent — What's Been Built

A plain-English walkthrough of everything that exists in this project today. Read it top to bottom to understand the whole system; skip to a section if you just need one piece.

---

## The one-line pitch

NexusAgent is a **private AI business OS** — a single React + FastAPI app that replaces Notion AI + Zapier + a CRM + a BI dashboard + an invoice tool, runs a **local LLM (Ollama)** by default, and only sends **redacted aggregates** to the cloud when you explicitly allow it. A team of **six named agents** works autonomously in the background and surfaces things for your approval.

---

## The cast — your six agents

Every agent has a name, a role, an emoji, a shift (schedule), and a rename-able identity. You can see them on the `/agents` page.

| Agent | Role | When it runs | What it does |
|-------|------|--------------|--------------|
| **Atlas** ☀️ | Chief of staff | Daily 08:00 | Writes a 1-page morning briefing — aggregates of tasks, overdue invoices, pipeline movement, deal changes |
| **Iris** 📬 | Inbox triage | Every 15 min | Reads new emails, classifies them, queues reply drafts for your approval |
| **Kira** 💰 | Invoice chaser | Daily 09:00 | Spots overdue invoices and drafts polite reminder emails (queued, never auto-sent) |
| **Arjun** 🎯 | Pipeline watcher | Daily 08:30 | Flags deals that haven't moved in 2+ weeks, suggests a next action |
| **Sage** 📎 | Meeting prep | Every 10 min | 30 min before a meeting, prepares a briefing on the contact and open deals |
| **Echo** 🧠 | Memory keeper | Weekly, Sunday 03:00 | Reviews conversation history and distils what's worth remembering |

You can **rename** any of them (they keep their behaviour, wear a new name), **pause** one that's noisy, or hit **Run now** to trigger it on demand.

---

## The four layers of privacy

Because the product runs on real business data, every outbound call passes through four gates before hitting any cloud provider. This lives in `config/privacy.py`.

1. **Kill switch** — `ALLOW_CLOUD_LLM=false` forces every call to local Ollama. One env flag, zero exceptions.
2. **Sensitivity routing** — any prompt that touches DB rows, customer records, or internal business data is flagged `sensitive=True` and routed to local, even if the cloud is configured.
3. **PII redaction** — emails, phones, Aadhaar/PAN/SSN numbers, credit cards, API keys, passwords, IP addresses, and file paths are replaced with opaque tokens like `[EMAIL_1]` *before* leaving the process. The mapping is kept locally so responses are un-redacted before you see them.
4. **Audit log** — every cloud call writes a line to `outputs/cloud_audit.jsonl` with the provider, model, SHA-256 fingerprint of the prompt, character count, and redaction count. **The raw prompt is never stored** — the log itself can't leak what it's protecting.

You can view all of this live on the `/security` page: current provider, kill switch state, redaction toggle, audit stats.

---

## How it talks to you

### Chat (`/chat`)

- **Smart Chat** — types out a streaming reply via the orchestrator (routes across intent → RAG → SQL → Report → What-If → Action).
- **Agent Mode** — a tool-using loop where the model picks tools (create task, draft email, run SQL, etc.) one step at a time. The UI shows which tools it called.
- **Slash commands** — `/remind`, `/task`, `/deal`, `/contact`, `/invoice`, `/brief`, `/triage` — type `/` for a typeahead menu. Each one rewrites your shortcut into a natural-language request the agent already handles.
- **Conversation persistence** — every turn auto-saves to SQLite; sidebar shows all conversations; click to load or delete.
- **Conversation export** — Markdown download or a rendered PDF via ReportLab.
- **Privacy badge under every reply** — shows "Cloud · 3 values redacted" or "Local · nothing left the machine" so you can see the privacy layer working turn by turn.

### Voice mode

- **Fullscreen hands-free** conversation with an animated orb that breathes when listening, pulses when thinking.
- **VAD-based listening** — no fixed 5-second cap; it decides when you're done speaking.
- **Whisper STT + browser TTS** — both run locally; nothing about your voice leaves the machine.

### Smart Inbox (`/inbox`)

One page for everything that needs *you* right now — pending approvals, proactive nudges, overdue tasks, today's meetings. Empty sections hide. Replaces five "notification centres" with one.

---

## The pages

Twenty-three React pages in `frontend/src/pages/`, roughly grouped:

**Always-on surfaces**
- `/` Dashboard — KPIs, today's agenda, latest briefing
- `/inbox` — unified approvals + nudges + tasks + meetings
- `/agents` — the team (rename, pause, Run now, History drawer)
- `/chat` — AI chat with slash commands + voice
- `/history` — past queries (search, filter by intent, star, re-run)

**Business surfaces**
- `/crm` · `/tasks` · `/invoices` · `/documents` — the Lead→Deal→Task→Invoice flow
- `/analytics` — charts off your real data
- `/reports` — PDF reports generated via the aggregate-then-cloud path

**Builders / explorers**
- `/workflows` — drag-and-drop React Flow builder, 10 pre-built templates
- `/whatif` — before/after simulator with a CFO-style critique
- `/database` — schema browser, stats, column statistics, data preview, CSV/Excel import
- `/sqleditor` — raw SQL editor (dev-mode only)
- `/memory` — business memory browser

**Team + trust**
- `/team` — roles, invitations, permissions, per-device sessions
- `/security` — cloud audit panel + 2FA enrollment + recovery codes
- `/auditlog` — full tool-call history, exportable to CSV

**Account**
- `/login` · `/acceptinvite` · `/resetpassword`
- `/settings` — developer-mode toggle, model config, temperature, maintenance

---

## Agent autonomy layer — the backend

### Scheduler (`agents/background/scheduler.py`)

Runs on APScheduler. Six jobs registered at boot, one per agent. Each job iterates over active businesses, checks whether the agent is enabled for that business, and wraps the run in the run log so you always know what happened.

### Run log (`agents/run_log.py`) — **new**

Every scheduled or on-demand agent run writes a row to `nexus_agent_runs` with status (`success` / `skipped` / `error`), items produced, and a trimmed error message on failure. Powers the "last ran" chip on the Agents page and the History drawer. Stores no prompts or customer data — just what the agent did and how it ended.

### Approvals (`agents/approval_queue.py`)

Nothing goes to the outside world without explicit approval. When an agent wants to send an email, write to Slack, create an invoice — it writes an approval row instead, and you review it in `/inbox`. Approve → the tool runs. Reject → the tool never runs.

### Nudges (`agents/nudges.py`)

Proactive signals: *"Kira noticed 2 overdue invoices — draft reminders?"* One click accepts (runs the agent), one click dismisses for the day.

### Tool registry (`agents/tool_registry.py`)

51 registered tools the agent loop can call: create task, add contact, draft invoice, send email (via approval), query SQL, embed document, run report, run what-if, etc. Each one is a normal Python function with a JSON schema the LLM can read.

### Business memory (`agents/business_memory.py`)

A searchable, per-business set of facts the agent remembers across conversations — customer preferences, pricing rules, internal terminology.

### Briefing (`agents/briefing.py`)

Collects local aggregates → redacts → sends only totals + top-5s to cloud for narrative writing → stores the snapshot so the dashboard shows it without re-running the LLM.

### Email triage (`agents/email_triage.py`)

Reads new IMAP messages, classifies each into `invoice_inquiry / sales_lead / support / spam / other`, and queues a reply draft for the appropriate ones.

### Research agent (`agents/research_agent.py`)

A multi-step research loop that plans → searches → reads → synthesises. Triggered from the agent chat when a question needs more than a single tool call.

---

## The provider abstraction

`config/llm_provider.py` is the single door every model call passes through. It auto-selects in this order:

1. **Anthropic Claude direct** — if `ANTHROPIC_API_KEY` is set
2. **Amazon Bedrock (Nova)** — if AWS keys are set
3. **Local Ollama** — always works, default fallback

Callers never care which is live. Three entry points:
- `invoke(prompt, sensitive=False)` — plain text → text
- `stream(prompt, sensitive=False)` — token-by-token generator
- `invoke_with_tools(messages, tools, ...)` — tool-calling loop

The `sensitive=True` flag forces local even if cloud is available. `fast=True` asks for a cheaper tier when one exists.

**Embeddings always stay local** via `nomic-embed-text` through Ollama — RAG never leaves your machine regardless of which chat LLM is active.

---

## The orchestrator (LangGraph)

`orchestrator/graph.py` is a directed graph that routes each user query through a chain:

`Tone Analyzer → Intent Detector → (RAG | SQL | Report | WhatIf | Action | Multi-Agent) → Synthesizer → Self-Reflection`

- **RAG Node** — ChromaDB-backed document retrieval with chunk deduplication and Jaccard source matching
- **SQL Node** — natural-language → SQL via the `sql_agent` subsystem, with self-correction loop and LRU cache (100 entries)
- **Action Node** — Discord / Slack / Email dispatch (always gated behind approval)
- **Report Node** — ReportLab PDF + Plotly charts from the aggregate-then-cloud path
- **What-If Node** — before/after numeric simulation
- **Multi-Agent Node** — fans out to specialist agents when a single pass isn't enough
- **Synthesizer** — stitches the pieces into a user-facing answer
- **Self-Reflection** — double-checks before sending

---

## The SQL agent (`sql_agent/`)

- `query_generator.py` — natural-language → SQL with few-shot examples, model prompt caching, schema-awareness
- `executor.py` — runs the query, samples rows, asks the LLM to explain the result (with `sensitive=True` because it sees real data)
- `schema_reader.py` — reflects the SQLite database into a compact schema blob the LLM can reason over
- `data_import.py` — CSV/Excel import pipeline with type detection, preview, protected-table guard

---

## Storage

Everything stays local unless you opt in.

- **SQLite** (`data/nexusagent.db`, WAL mode) — business data, CRM, invoices, tasks, approvals, personas, run log, conversations, query history, nudges, agent memory, audit log
- **ChromaDB** (`chroma_db/`) — vector store for RAG (documents, knowledge base)
- **Filesystem** (`outputs/`) — generated PDFs, exported conversations, cloud audit JSONL

The SQLite schema is managed by `sql_agent/db_setup.py` + each agent module's `CREATE TABLE IF NOT EXISTS` on first use.

---

## Authentication + multi-tenancy

- **JWT auth** via `api/auth.py`
- **Multi-tenant** — every query is scoped by `X-Business-Id`. A user can belong to multiple businesses with different roles (owner / admin / member / viewer).
- **Invitations + onboarding** — email invite → accept page → join business
- **2FA** — TOTP enrolment + QR code + recovery codes, per `api/security.py`
- **Per-device sessions** — see active sessions on `/team`, revoke individually

---

## What the API exposes

The FastAPI server (`api/server.py`) is one file with ~2500 lines; highlights:

- **Agents** — `/api/agents/personas`, `/api/agents/{key}/run`, `/api/agents/runs`, `/api/agents/activity`, `/api/agents/nudges`, `/api/agents/background`
- **Chat** — `/api/chat` (orchestrator), `/api/agent/chat` (tool-loop), `/api/agent/tools`
- **Privacy** — `/api/privacy/status`, `/api/privacy/audit`, `/api/privacy/audit/clear`
- **Approvals** — `/api/approvals`, approve / reject endpoints
- **CRM / Tasks / Invoices / Documents** — standard REST
- **Analytics** — `/api/analytics/*` including `/agent-impact`
- **Reports** — `/api/reports/generate`, `/api/reports/download`
- **Workflows** — `/api/workflows/*` with scheduler jobs + history
- **Audit** — `/api/audit/export` (CSV)

---

## Testing

- **66 passing pytest tests** across `tests/` — 50 core, 9 privacy, 7 run_log + privacy stats
- Covers the orchestrator, SQL self-correction, RAG retrieval, redaction, kill switch, run-log lifecycle, routing decisions
- Frontend builds cleanly via Vite

Run them all: `python -m pytest tests/ -v`

---

## The UI system

- **Dark theme with CSS variables** (`--color-accent`, `--color-surface-1`, `--color-border`, etc.) — easy to reskin
- **Panel-based layout** with consistent gradient headers, pill badges, and micro-animations
- **Reusable styles** via `App.css` + component-level style objects
- **Lucide React** icon set
- **React Flow** for the workflow builder
- **React Markdown** for rendering assistant messages

---

## Shortcuts that earn their keep

- `/` in chat opens a slash-command menu
- **Run Now** on any agent card triggers it immediately
- **Pause** any agent that's being too noisy; resume when you want it back
- **History** drawer on each agent shows the last 50 runs with error details
- **Empty Inbox** means you're actually done — there is no busywork feed
- **Developer mode** toggle in Settings hides power-user pages from your less-technical teammates

---

## The build in three numbers

- **~2,500 lines** — FastAPI server
- **~15,000 lines** — Python across agents, orchestrator, SQL agent, RAG, tools, config
- **~12,000 lines** — React frontend across 23 pages + components + services

Running it: `start.bat` (Windows) — boots Ollama, the FastAPI server, and the Vite dev server. Or manually: `streamlit run ui/app.py` for the Streamlit variant, `uvicorn api.server:app --reload` + `npm run dev` for the React stack.

---

## The most recent additions (2026-04-24)

Added today:

- **Agent run log** (`agents/run_log.py`) — every scheduled or manual run records status, items produced, duration, and errors
- **Per-agent pause / resume** — honored by the scheduler; disabled runs show as `skipped` in the log
- **History drawer** on the Agents page — last 50 runs for each agent with error details
- **In-chat privacy badge** — every assistant reply now shows "Cloud · N values redacted" or "Local · nothing left the machine"
- **Bedrock privacy gap closed** — Bedrock `invoke` + `stream` now go through the same redaction + audit + restore pipeline as Claude (was previously skipping it)
- **Privacy stats contextvar** — per-request counters of redactions, providers hit, and kill-switch activations; surfaces cleanly into any chat response

---

## Where to go next

A few directions, roughly ordered by payoff:

1. **Interval override UI** — let users change "email triage every 15 min" to "every hour" without editing code
2. **Multi-step workflow chaining** — `triage email → extract task → draft reply → queue for approval` saved as a workflow
3. **Anomaly detection on imported data** — agent watches the DB, flags outliers, posts to inbox
4. **Wake-word + streaming TTS** for voice mode — turn it from turn-based into conversational
5. **NL→SQL eval harness** — golden queries + expected results, run on every change
6. **Plugin/tool marketplace** — per-tool approval policies so you can wire Slack / Gmail / Notion with different trust levels

That's the full picture. Open any file from the directory column of the page you're curious about — everything's wired the same way.
