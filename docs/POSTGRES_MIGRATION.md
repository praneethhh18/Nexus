# SQLite → Postgres migration playbook

Status as of 2026-04-29:

| Piece | State |
|---|---|
| `config/db.py` — backend-agnostic connection wrapper | ✅ Built, supports `sqlite3.Row`-style indexing on Postgres |
| `tools/migrate_to_postgres.py` — one-shot data migration | ✅ Built |
| `psycopg[binary]>=3.1` driver | ✅ Pinned in `requirements.txt` |
| **Modules using `config.db.get_conn()`** | 🟡 **1 of 60** (`config/cloud_budget.py`) |
| **Tests passing on Postgres** | ✅ `tests/test_cloud_budget.py` (6/6) |
| `.env` `DATABASE_URL` toggle | ✅ Documented, commented out by default |

This doc is the file-by-file recipe for migrating the remaining ~59 files. Each
file takes 5–15 minutes if you follow the pattern.

---

## 1 — Why the abstraction, not raw psycopg

NexusAgent has 60+ files using `sqlite3.connect(DB_PATH)` directly. Switching
the whole codebase to psycopg in one PR would touch every one of them and
risk bugs nobody can review well. Instead `config/db.py` exposes a wrapper
that:

- Accepts SQLite-flavored SQL (`?` placeholders, `INTEGER PRIMARY KEY AUTOINCREMENT`,
  `datetime('now')`) and translates on the fly for Postgres
- Mimics the `sqlite3.Connection` API (`.execute`, `.commit`, `.row_factory`,
  context manager, etc.) so existing code that uses `conn.row_factory = sqlite3.Row`
  keeps working
- Falls back to native SQLite when `DATABASE_URL` is unset

So you migrate one file at a time and tests on both backends prove parity at
each step. No big-bang refactor.

---

## 2 — The pattern (do this for each file)

### Step 1: change the imports

```python
# before
import sqlite3
from pathlib import Path
from config.settings import DB_PATH

# after
from config.db import get_conn
```

You usually keep `import sqlite3` if and only if the file references
`sqlite3.Row` (for row-factory). The `Path` and `DB_PATH` imports go away
unless used elsewhere.

### Step 2: change the connection helper

```python
# before
def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    # ... DDL ...
    return conn

# after
def _conn():
    conn = get_conn()
    # PRAGMAs are silently no-op'd on Postgres by config/db.py — leave them
    # if you want, or strip. DDL stays SQLite-flavored; the wrapper translates.
    # ... DDL ...
    return conn
```

You drop the `Path(DB_PATH).parent.mkdir(...)` because Postgres doesn't need
it and `config/db.py` already does the SQLite parent-mkdir.

### Step 3: leave the rest of the file alone

`?` placeholders, `INSERT INTO ... (?,?,?)`, `conn.row_factory = sqlite3.Row`,
`conn.execute(...)`, `cursor.fetchone()`, `row["column"]` — all of these
already work on both backends.

### Step 4: SQLite-specific patterns that DO need rewriting

The wrapper handles common cases but a few things you have to fix manually:

| SQLite | Postgres-compatible replacement |
|---|---|
| `INSERT OR REPLACE INTO t (k, v) VALUES (?, ?)` | `INSERT INTO t (k, v) VALUES (?, ?) ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v` |
| `INSERT OR IGNORE INTO t ...` | `INSERT INTO t ... ON CONFLICT DO NOTHING` |
| `cursor.lastrowid` | `cursor.execute("INSERT ... RETURNING id"); cursor.fetchone()[0]` |
| `RANDOM()` | `RANDOM()` works on both. (No change needed.) |
| `datetime('now')` | Already auto-translated to `NOW()` |
| `julianday(...)` / `strftime(...)` | Use Python `datetime` and pass strings instead |
| `WITHOUT ROWID` | Drop it — Postgres ignores |

The 11 files that use these patterns (as of 2026-04-29) are listed in
section 6 below.

### Step 5: test on both backends

```bash
# SQLite (default)
python -m pytest tests/test_<your_module>.py -v

# Postgres
DATABASE_URL=postgresql://nexus:nexuspw@localhost:5434/nexusagent \
  python -m pytest tests/test_<your_module>.py -v
```

If both pass, the migration is complete for that file. Commit, move on.

---

## 3 — Reference example: `config/cloud_budget.py`

The completed POC. Before/after diffs:

```diff
-import sqlite3
-from pathlib import Path
+from config.db import get_conn

-from config.settings import DB_PATH
```

```diff
-def _conn() -> sqlite3.Connection:
-    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
-    conn = sqlite3.connect(DB_PATH)
+def _conn():
+    conn = get_conn()
```

That's it. Two import changes, one function-body simplification. Tests pass
on SQLite *and* Postgres without any test-code changes.

---

## 4 — Recommended migration order

Do these in this order — small + isolated first, then the bigger CRUD
modules. Each row links to the file. Tick the box as you finish.

### Phase A — small leaf modules (1–2 hr total)
- [x] `config/cloud_budget.py` (done — POC)
- [ ] `agents/run_log.py`
- [ ] `agents/activity.py`
- [ ] `agents/business_memory.py`
- [ ] `memory/conversation_store.py`
- [ ] `memory/query_history.py`
- [ ] `memory/user_memory.py`
- [ ] `memory/long_term.py`

### Phase B — auxiliary tables (2–3 hr)
- [ ] `api/whatsapp.py` (history table + accounts/tokens)
- [ ] `api/notification_prefs.py`
- [ ] `api/integrations.py`
- [ ] `api/onboarding.py`
- [ ] `api/setup_wizard.py`
- [ ] `api/saved_queries.py`
- [ ] `api/tags.py`
- [ ] `api/agent_schedule.py`
- [ ] `api/custom_agents.py`
- [ ] `api/security.py` (audit log table)
- [ ] `api/usage_metrics.py`
- [ ] `api/data_export.py`
- [ ] `api/activity_feed.py`
- [ ] `api/team.py`
- [ ] `api/calendar.py`
- [ ] `api/documents.py`
- [ ] `api/entity_import.py`
- [ ] `api/notifications.py`
- [ ] `api/reliability.py`
- [ ] `api/auth.py`
- [ ] `api/analytics.py`
- [ ] `api/suggestions.py`
- [ ] `api/rag_collections.py`
- [ ] `api/seed_data.py`

### Phase C — core CRUD (1 day, careful)
- [ ] `api/crm.py` (contacts + companies + deals + interactions)
- [ ] `api/businesses.py`
- [ ] `api/smtp_credentials.py` (uses Fernet — verify encryption key is portable)

### Phase D — agents and tools
- [ ] `agents/personas.py`
- [ ] `agents/summarizer.py`
- [ ] `agents/email_triage.py`
- [ ] `agents/briefing.py`
- [ ] `agents/nudges.py`
- [ ] `agents/background/scheduler.py`
- [ ] `agents/background/invoice_reminder.py`
- [ ] `agents/background/meeting_prep.py`
- [ ] `agents/background/stale_deal_watcher.py`

### Phase E — routers
- [ ] `api/routers/forge.py`
- [ ] `api/routers/bant.py`
- [ ] `api/routers/lead_scoring.py`
- [ ] `api/routers/email_paste.py`
- [ ] `api/routers/backup.py`

### Phase F — SQL agent
- [ ] `sql_agent/data_import.py`
- [ ] `sql_agent/executor.py`
- [ ] `sql_agent/db_setup.py`

### Phase G — workflows + tools + tests
- [ ] `workflows/scheduler.py`
- [ ] `tools/backup_db.py`
- [ ] Tests that use raw `sqlite3.connect()` for fixtures

---

## 5 — Migrating data once code is ready

When all phases above are complete:

1. Stop the API server.
2. Set `DATABASE_URL` in `.env` to your Postgres DSN.
3. Run:
   ```bash
   python tools/migrate_to_postgres.py --dry-run
   ```
   Verify the output looks sane — every table from your SQLite DB
   should be listed.
4. Run for real:
   ```bash
   python tools/migrate_to_postgres.py
   ```
   This creates Postgres tables that mirror your SQLite schema and
   copies rows in batches of 500.
5. Restart the API server. It now talks to Postgres exclusively.
6. Keep the SQLite file (`data/nexusagent.db`) as a backup until you've
   confirmed Postgres is healthy under real load for at least a week.

---

## 6 — Files with SQLite-specific SQL that need manual rewrites

As of 2026-04-29, these 11 files use `INSERT OR REPLACE`, `INSERT OR IGNORE`,
`lastrowid`, or `datetime('now')` (the last is auto-translated, but the
others aren't):

- `memory/user_memory.py`
- `memory/query_history.py`
- `agents/nudges.py`
- `api/setup_wizard.py`
- `api/security.py`
- `api/tags.py`
- `api/team.py`
- `api/suggestions.py`
- `api/businesses.py`
- `sql_agent/db_setup.py`

Look for these specific tokens via grep and rewrite per the table in
section 2, step 4.

---

## 7 — How to test parity continuously

Add this make-target / shell alias so it's one command:

```bash
# tests/run_dual.sh
set -e
echo "── SQLite ──"
python -m pytest tests/ -q --tb=short --timeout=60

echo "── Postgres ──"
DATABASE_URL=postgresql://nexus:nexuspw@localhost:5434/nexusagent \
  python -m pytest tests/ -q --tb=short --timeout=60
```

CI doesn't run this yet — once at least Phase A is done, add a Postgres
matrix dimension to `.github/workflows/ci.yml` so every PR runs both.

---

## 8 — Things this migration does NOT do

- **Foreign keys.** SQLite is loose about FKs; Postgres is strict. If the
  schema needs FK constraints, add them by hand after migration.
- **Indexes beyond primary keys.** `migrate_to_postgres.py` doesn't recreate
  the secondary indexes — they're set by each module's `CREATE INDEX IF NOT EXISTS`
  on first run, which fires when you boot the API against Postgres.
- **Triggers, views, stored procedures.** NexusAgent has none, so this is
  a non-issue.
- **Connection pooling.** `config/db.py` opens a connection per call. For
  production that's fine for moderate traffic but eventually wants pgBouncer
  or a proper pool. Out of scope for this migration; add when needed.
