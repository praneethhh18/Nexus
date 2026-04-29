# NexusAgent — Architecture & Contributor Guide

This document is for engineers who will read, extend, or audit the codebase.
For end-user docs, see [`README.md`](../README.md). For change history, see
[`CHANGELOG.md`](./CHANGELOG.md). For contribution rules, see
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 1. What this codebase is

A private, local-first AI business OS for small teams. One web app replaces
a typical patchwork of Notion AI + Zapier + an analytics dashboard + a CRM +
an invoice tool — with the constraint that **customer data never leaves the
machine**, while reports still get cloud-quality writing through a strict
aggregate-only path.

The product runs as **two long-lived processes**:

1. **FastAPI backend** (`api/server.py`) — Python 3.11+, Uvicorn, SQLite,
   ChromaDB, LangGraph, APScheduler.
2. **React frontend** (`frontend/`) — React 19, Vite, Tailwind, React Flow,
   React Router. Talks to the backend over REST + a single WebSocket for
   streaming chat.

The **Electron wrapper** (`desktop/`) bundles both into one installable app
with a tray icon, a global hotkey, and a first-run wizard that gets Ollama
ready. The **landing site** (`landing/`) is a separate Vite SPA for the
marketing page.

---

## 2. Top-level layout

```
NexusAgent/
├── api/                FastAPI app + 35+ feature routers
│   ├── server.py       app assembly, middleware, lifespan, websocket
│   └── routers/        one file per feature surface
├── orchestrator/       LangGraph state graph + intent + multi-agent
├── agents/             named agent personas + scheduler + run log
│   ├── background/     APScheduler job runner
│   └── tools/          tool registry the agents are allowed to call
├── sql_agent/          NL→SQL, schema reader, executor, CSV/Excel import
├── rag/                ingestion, embeddings, ChromaDB, multi-doc retrieval
├── action_tools/       email, Discord, desktop notifications, file dispatch
├── report_generator/   Plotly + ReportLab PDF + aggregate-then-cloud narrative
├── voice/              faster-whisper STT, pyttsx3 TTS, tone analyzer
├── memory/             conversations, query history, user memory, audit
├── workflows/          node registry + executor + scheduler + templates
├── config/             settings, LLM provider, privacy gate, db helpers
├── utils/              what-if simulator, exporters, helpers
├── frontend/           React + Vite app
│   ├── src/pages/      one file per route (25 pages)
│   ├── src/components/ shared UI + Layout shell
│   └── src/services/   API client wrappers, one per backend surface
├── desktop/            Electron main + tray + hotkey + Ollama bridge
├── landing/            marketing site (separate Vite SPA)
├── tests/              17 test files, 72+ unit tests + e2e + Playwright
├── docs/               ADRs, design notes, this file
├── deploy/             nginx config, deployment helpers
├── data/               SQLite DB + uploaded documents (gitignored)
├── chroma_db/          vector store (gitignored)
├── outputs/            generated PDFs, reports, audit log (gitignored)
├── Dockerfile          two-stage build: frontend → python image
└── docker-compose.yml  full stack including Ollama
```

Anything under `venv/`, `node_modules/`, `data/`, `chroma_db/`, `outputs/`,
`frontend/dist/`, `landing/dist/` is ignored or generated.

---

## 3. Request lifecycle (chat)

```
   browser
     │  POST /api/chat  { message, conversation_id, ... }
     ▼
   FastAPI middleware
     │  auth → rate limit → privacy.reset_stats() → enter request
     ▼
   intent_detector.classify(text)
     │            ↓
     ├── "sql"     → sql_agent.query_generator → executor (local-only)
     ├── "rag"     → rag.retriever → multi_document_rag
     ├── "action"  → approval_queue.enqueue (no outbound until approved)
     ├── "report"  → report_generator.narrative (aggregate-then-cloud)
     ├── "agent"   → orchestrator.multi_agent (planner → specialists)
     └── "chat"    → llm_provider.invoke
     ▼
   privacy.prepare_for_cloud(prompt)   if cloud route is allowed
     │  redact → audit_cloud_call → invoke
     ▼
   privacy.restore_from_cloud(response, mapping)
     ▼
   privacy.get_stats()  → attached to response.privacy
     ▼
   { reply, citations, tools_called, privacy: { provider, redactions, ... } }
```

The privacy layer is the choke point — every cloud-bound call goes through
`config/privacy.prepare_for_cloud`. Sensitive callers pass `sensitive=True`
which forces local Ollama regardless of the kill switch.

See [`config/privacy.py`](../config/privacy.py) and
[`tests/test_privacy.py`](../tests/test_privacy.py).

---

## 4. Module map

### `config/`

| File | Purpose |
|---|---|
| `settings.py` | typed `.env` loader; everything else imports from here |
| `llm_provider.py` | Ollama / Claude / Bedrock provider abstraction |
| `llm_tools.py` | tool-calling wrapper (handles content blocks + redaction across tool_results) |
| `llm_bedrock.py` | Bedrock-specific provider, also redacts and audits |
| `privacy.py` | the four-defense gate — kill switch, routing, redaction, audit, per-request stats |
| `db.py` | SQLite connection helper with row factory |

### `api/`

`server.py` mounts middleware (CORS, rate limit, request id) and includes
every router under `api/routers/`. There are 35+ routers, one per feature
surface. The split was finished in 2.1.0. Adding a new feature surface =
create one file under `api/routers/` and include it in `server.py`.

### `orchestrator/`

LangGraph state graph used for non-trivial chat. `multi_agent.PlannerAgent`
decomposes complex tasks across `DataAgent`, `DocAgent`, and
`SynthesisAgent`.

### `agents/`

Six named personas with run logs and schedules:

- `personas.py` — display names, enabled flags, icons. User-editable.
- `background/scheduler.py` — APScheduler with cron triggers pinned to
  `SCHEDULER_TZ`. Every per-business run is wrapped in
  `run_log.start/finish` so the History drawer reflects reality.
- `run_log.py` — `nexus_agent_runs` table; helpers: `start`, `finish`,
  `list_runs`, `last_run`, `summary`. Error strings trimmed to 800 chars.

When you add a new background agent:

1. Register the persona in `personas.PERSONAS`.
2. Wrap the work function in `run_log.start(...)` / `.finish(...)`.
3. Mark sensitive callers with `sensitive=True`.

### `sql_agent/`

NL→SQL on local SQLite. `query_generator.py` ships the schema and the
question through Ollama (sensitive=True), `executor.py` runs the SQL,
`schema_reader.py` reflects the DB. `data_import.py` is the CSV/Excel
ingest path with type detection and a protected-table guard.

`_explain_result` in `executor.py` is the only place that sees DataFrame
sample rows — it is hard-coded `sensitive=True`. Do not remove that flag.

### `rag/`

`ingestion.py` parses PDF/DOCX/TXT into LangChain `Document` chunks,
`embedder.py` batches them through `nomic-embed-text` (always local),
`vector_store.py` persists to ChromaDB, `retriever.py` re-ranks the
top-K with the LLM, `multi_document_rag.py` does cross-doc synthesis and
contradiction detection.

### `report_generator/`

The aggregate-then-cloud pipeline:

1. SQL runs locally.
2. `narrative.compute_aggregates(df)` reduces the DataFrame to totals,
   means, mins, maxes, and top-5 category breakdowns. Row data is
   discarded.
3. Category labels are run through `privacy.redact` (reversible map).
4. Only the redacted aggregate dict is sent to the cloud LLM.
5. The response is un-redacted locally before display.

Cloud calls in this path are 20–50× smaller than a full-row prompt — that
is why latency is low and cost stays predictable.

### `workflows/`

n8n-style automation. `node_registry.py` declares 20+ node types,
`executor.py` runs them with topological sort + branching, `scheduler.py`
runs scheduled workflows, `templates.py` ships 10 pre-built recipes,
`storage.py` persists workflow definitions as JSON in SQLite.

### `voice/`

`listener.py` wraps `faster-whisper` for STT, `speaker.py` wraps `pyttsx3`
for TTS, `tone_analyzer.py` tags incoming voice with mood. All local.

### `memory/`

- `conversation_store.py` — chat persistence (SQLite)
- `query_history.py` — searchable query history
- User memory, patterns, and the audit logger

### `frontend/src/`

- `pages/` — 25 routes, lazy-loaded. The big ones: `Chat.jsx`, `Inbox.jsx`,
  `Agents.jsx`, `CRM.jsx`, `Invoices.jsx`, `Workflows.jsx`, `Security.jsx`,
  `Settings.jsx`.
- `components/Layout.jsx` — sidebar + topbar shell.
- `services/` — one client module per backend surface.

---

## 5. Privacy contract

> No row-level customer or business data leaves the machine, ever.

| Layer | What it does |
|---|---|
| 1. Kill switch (`ALLOW_CLOUD_LLM=false`) | hard-disables every cloud call |
| 2. Sensitivity routing | `sensitive=True` forces a request to local Ollama even when cloud is enabled |
| 3. Redaction | `privacy.prepare_for_cloud` runs every outbound prompt through PII regexes (email, phone, Aadhaar, PAN, SSN, cards, IPs, paths, secrets); returns a reversible map |
| 4. Audit | every cloud call appends one line to `outputs/cloud_audit.jsonl` with provider, model, SHA-256, redaction count and kinds — never the raw prompt |

Code locations:

- Implementation: `config/privacy.py`
- Tests: `tests/test_privacy.py` (9 tests, must stay green)
- Sensitive callers (do not remove `sensitive=True`):
  - `sql_agent/executor.py::_explain_result`
  - `sql_agent/query_generator.py`
  - `agents/email_triage.py::_classify`

If you add a new code path that calls an LLM, call
`privacy.note_call(provider, cloud, redactions, kinds)` so the in-chat
privacy badge stays accurate.

---

## 6. Local development

```bash
# 1. Backend
python -m venv venv
venv\Scripts\activate                         # Windows
pip install -r requirements.txt
uvicorn api.server:app --reload --port 8000

# 2. Frontend
cd frontend
npm install
npm run dev                                   # http://localhost:5173

# 3. Ollama (required)
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull nomic-embed-text
ollama serve

# 4. (Optional) Desktop wrapper
cd desktop
npm install
npm run dev                                   # Electron pointing at :5173
```

`start.bat` ties steps 1–3 together for Windows.

### Useful environment variables

| Var | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | local LLM endpoint |
| `OLLAMA_MODEL` | `llama3.1:8b-instruct-q4_K_M` | default model |
| `EMBED_MODEL` | `nomic-embed-text:latest` | embeddings (always local) |
| `ALLOW_CLOUD_LLM` | `true` | privacy kill switch |
| `REDACT_PII` | `true` | toggle redaction (leave on) |
| `AUDIT_CLOUD_CALLS` | `true` | append to `outputs/cloud_audit.jsonl` |
| `SCHEDULER_TZ` | `Asia/Kolkata` | timezone for cron triggers |
| `JWT_SECRET` | autogenerated | persisted to `data/.jwt_secret` if missing |
| `NEXUS_DEMO` | `0` | when `1`, loads sandbox seed data and skips auth |

---

## 7. Tests

```bash
# Fast unit suite (no Ollama)
python -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_tier1_features.py

# Full suite incl. e2e (requires Ollama)
python tests/test_e2e.py

# Frontend e2e (Playwright, 10 critical flows)
cd frontend
npx playwright test
```

CI runs the unit suite + Playwright on every push. Privacy tests are
non-negotiable — a red `test_privacy.py` blocks merge.

---

## 8. Conventions

- Don't add error handling for scenarios that can't happen. Trust internal
  code; validate only at boundaries.
- Default to no comments. Add one only when the *why* is non-obvious.
- One router per feature surface. Don't grow `api/server.py`.
- One service module per backend surface in `frontend/src/services/`.
- Lazy-load every page; main bundle stays under 200 KB.
- Run the privacy tests before committing changes that touch any LLM caller.
- Commit messages: short imperative subject, lowercase, no body unless
  truly needed. Push to `main`. Solo project; no PR workflow.

---

## 9. Where to start reading

If you have an hour, read in this order:

1. [`README.md`](../README.md) — what the product is.
2. `config/privacy.py` — the contract.
3. `api/server.py` — how routers are assembled.
4. `agents/background/scheduler.py` — how scheduled work runs.
5. `orchestrator/multi_agent.py` — how complex tasks are split.
6. `frontend/src/pages/Chat.jsx` — the main user surface.
7. `frontend/src/pages/Inbox.jsx` — the second main user surface.
8. `tests/test_privacy.py` — the guarantees the product makes.

That is the entire load-bearing skeleton. Everything else is leaves.
