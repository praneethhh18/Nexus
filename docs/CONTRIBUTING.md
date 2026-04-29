# Contributing to NexusAgent

Thanks for looking. This doc covers the shape of the codebase + the expectations around any patch you send.

## Repo layout

```
NexusAgent/
├── api/                # FastAPI backend — one file per domain (auth, crm, tasks, ...)
│   ├── server.py       # App bootstrap + middleware + cross-cutting endpoints
│   └── routers/        # Per-domain routers (being extracted from server.py)
├── agents/             # Autonomous agent logic: personas, scheduler, run log, approvals
│   └── background/     # Scheduled agents (stale_deal_watcher, invoice_reminder, meeting_prep)
├── orchestrator/       # LangGraph chat orchestrator (intent → RAG | SQL | action | report)
├── rag/                # Vector store + retriever + ingestion + multi-doc comparison
├── sql_agent/          # NL → SQL generation with self-correction
├── report_generator/   # ReportLab + Plotly PDF reports
├── workflows/          # Drag-and-drop workflow engine (nodes, executor, storage)
├── voice/              # Whisper STT + browser-TTS glue
├── memory/             # Conversation store, audit logger, query history
├── tools/              # Agent tools (email, discord, slack, file dispatch)
├── utils/              # Shared helpers (timez, sample docs, notifications)
├── frontend/           # React + Vite app
│   ├── src/pages/      # One file per route
│   ├── src/components/ # Reusable UI (EmptyState, Skeleton, ToastHost, ErrorBoundary, ...)
│   ├── src/services/   # Typed API clients
│   └── e2e/            # Playwright E2E suite
├── landing/            # Separate Vite project for the public marketing site
├── desktop/            # Electron wrapper (tray, hotkey, Ollama detection)
├── tests/              # Pytest suite — one file per feature group
└── deploy/             # Docker, helm, one-click deploy configs
```

## Quick start for development

```bash
# Backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn api.server:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run e2e          # Playwright against mocked backend

# Landing page (optional)
cd landing
npm install && npm run dev     # http://localhost:4000
```

Start Ollama separately if you want real inference; without it the LLM paths will fall back to error messages but the UI still renders.

## Code conventions

### Python

- **Timestamps**: use `utils.timez.now_iso()` / `now_utc_naive()` — never `datetime.utcnow()`, which is deprecated in 3.12+.
- **DB access**: every tenant table has `business_id`. Every `SELECT` / `UPDATE` / `DELETE` that returns rows MUST filter by `business_id` + whatever tenancy constraint applies. Cross-tenant reads are a P0 bug.
- **Errors from agent tools**: never raise; return `{"error": "..."}` so the agent loop can keep going. The approval queue + audit log will capture the failure.
- **Secrets in config**: store under any key matching `*secret*`, `*token*`, `*key*`, `*password*`. The integration framework auto-masks those in API responses.
- **Modules > 600 lines**: break them up. `server.py` is in-flight being split into routers; avoid adding new endpoint groups directly to it.

### Frontend

- **One page per route.** If a page is >600 lines, extract subcomponents into `pages/<Page>/`.
- **API services** live in `src/services/<domain>.js` with typed functions. No inline `fetch` in components.
- **Styling**: use the CSS variables in `src/index.css` (`var(--color-accent)`, etc.). Light theme kicks in when `[data-theme="light"]` is set.
- **Toasts**: `import { toast } from './components/ToastHost'` — don't roll your own.
- **Empty states**: use `<EmptyState icon={...} title="..." description="..." primaryLabel="..." onPrimary={...} />`.
- **Loading states**: use `<Skeleton>`, `<SkeletonText>`, `<SkeletonCard>`. Never show raw spinners on first paint.

### Commits

- Simple, short commit messages in lowercase. No `feat:` / `fix:` prefixes required. No Claude / AI attribution.
- Push straight to `main` for solo work; open a PR once there's another collaborator.

## Tests

Running the full suite:

```bash
python -m pytest tests/ -q                     # backend (225+ tests)
cd frontend && npm run e2e                     # Playwright (27 tests)
cd frontend && npm run build                   # verify bundle builds
cd landing && npm run build                    # verify landing builds
```

Every new feature that touches data must come with a pytest file. E2E specs are for user-visible flows only — don't reach for them when a unit test would catch the same bug.

## Database migrations

Schema changes go through `db/migrate.py` — a small handwritten runner (no Alembic, no SQLAlchemy ORM). On every server boot, `apply_pending()` runs any new migration files and records them in the `nexus_migrations` ledger.

**To add a migration:**

```bash
# 1. Pick the next version number (current max + 1, four-digit padded).
ls db/migrations/    # check existing

# 2. Write the file.
$EDITOR db/migrations/0002_add_foo_column.sql
```

```sql
-- 0002_add_foo_column.sql
ALTER TABLE nexus_widgets ADD COLUMN foo TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_widgets_foo ON nexus_widgets(foo);
```

```bash
# 3. Apply (or just restart the server — the boot does this automatically).
python -m db.migrate

# Or check what's pending without applying.
python -m db.migrate --status
```

**Rules of the road:**

- **Never edit a migration after it's shipped.** The runner notices (SHA mismatch) and warns, but it can't undo the change for users who already applied it. Add a follow-up migration instead.
- **Make statements idempotent where you can** — `IF NOT EXISTS`, `IF EXISTS`, `INSERT OR IGNORE`. SQLite's transactional DDL has gotchas, so a partial-failure-safe migration is much easier to recover from.
- **One concern per migration.** If you're adding a column AND backfilling values, that's two files: `0003_add_status_column.sql` and `0004_backfill_status.sql`. Keeps blast radius small.
- **The 0001 baseline is intentionally empty.** It's the marker for "the schema as it shipped at v2.0." All future schema lives in 0002+.

The legacy `CREATE TABLE IF NOT EXISTS` calls scattered in `api/*.py` modules still create tables on first boot for new workspaces. The migration runner is for *changing* the schema after v2.0 — adding columns, indexes, drops, renames.

## Privacy invariants (non-negotiable)

1. Embeddings are **always** local via Ollama. Never send raw documents to a cloud embedder.
2. Any prompt touching DB rows / customer records passes `sensitive=True` to `config.llm_provider.invoke()`. That forces local LLM even if cloud is configured.
3. The cloud audit log never stores raw prompt text — only SHA-256 fingerprints + counts. If you add a new cloud call path, it MUST call `privacy.audit_cloud_call(...)`.
4. Multi-tenant isolation: every SQL query `WHERE business_id = ?`. No exceptions.

Break any of these and you've broken the product's whole promise.

## Architecture Decision Records

See `docs/adr/` for the big "why we did X" decisions. Add a new one (`NNNN-title.md`) when you make a call that will puzzle a future contributor.

## Getting help

Open a GitHub Discussion or file an issue. No Slack, no Discord yet — we'd rather keep conversations searchable.
