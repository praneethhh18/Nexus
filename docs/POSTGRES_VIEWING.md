# How to view data in your local PostgreSQL

You have PostgreSQL 18 running on **localhost:5434**, with:

- **Superuser**: `postgres` / (your install password — we don't use this)
- **App user**: `nexus` / `nexuspw`
- **Database**: `nexusagent`
- **Connection string**: `postgresql://nexus:nexuspw@localhost:5434/nexusagent`

This guide covers the three ways to look at your data, ordered easiest → most powerful.

---

## Option 1 — pgAdmin 4 (graphical, easiest)

You already have this installed. It's a full-featured database browser with point-and-click everything.

### First-time setup of the connection

1. Open **pgAdmin 4** from your Start menu
2. When asked, enter the master password you set when first using pgAdmin (this is pgAdmin's own password, not Postgres)
3. In the left sidebar:
   - **Right-click "Servers"** → **Register** → **Server…**
4. **General tab**: Name it anything, like `NexusAgent (local)`
5. **Connection tab**:
   - Host name/address: `localhost`
   - Port: `5434`
   - Maintenance database: `nexusagent`
   - Username: `nexus`
   - Password: `nexuspw`
   - Tick **Save password** so you don't type it every time
6. Click **Save**

A green dot appears next to your new server. You're connected.

### Browsing tables

Expand the tree:
```
NexusAgent (local)
└─ Databases
   └─ nexusagent
      └─ Schemas
         └─ public
            └─ Tables          ← double-click here
```

You'll see every NexusAgent table: `nexus_contacts`, `nexus_invoices`, `nexus_cloud_usage`, `nexus_whatsapp_history`, etc.

### Viewing rows

**Right-click any table → View/Edit Data → All Rows**

A spreadsheet-style grid opens. You can:
- Click any cell to edit it (saves on Tab/Enter)
- Right-click row headers → **Delete row**
- Sort by clicking column headers
- Filter via the **Filter** icon in the toolbar

For tables with millions of rows, use **First 100 Rows** instead of **All Rows** — much faster.

### Running queries (the power tool)

**Right-click `nexusagent` database → Query Tool**

Paste any SQL and press **F5** (or click the ▶ play icon):

```sql
-- All contacts in business "biz-a"
SELECT * FROM nexus_contacts WHERE business_id = 'biz-a';

-- Today's cloud LLM spend across all businesses
SELECT business_id, SUM(tokens_in + tokens_out) AS total_tokens, ROUND(SUM(est_cost_usd)::numeric, 4) AS spend_usd
FROM nexus_cloud_usage
WHERE date = CURRENT_DATE::text
GROUP BY business_id
ORDER BY total_tokens DESC;

-- WhatsApp conversation memory for a specific phone
SELECT role, content, ts FROM nexus_whatsapp_history
WHERE phone = '916360218968' ORDER BY id;
```

Results appear in the bottom pane. **Right-click a result → Save as CSV** to export.

### Tips

- **Refresh a table after data changes**: right-click table → **Refresh**
- **Schema diagrams**: right-click a table → **ERD For This Table** — auto-renders foreign-key relationships
- **Backup**: right-click database → **Backup…** → choose a `.sql` or `.tar` file
- **Restore**: right-click database → **Restore…**

---

## Option 2 — psql (command-line, fast)

For one-off lookups without launching pgAdmin. Already installed at `C:\Program Files\PostgreSQL\18\bin\psql.exe`.

### Connect

```powershell
$env:PGPASSWORD = "nexuspw"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U nexus -h localhost -p 5434 -d nexusagent
```

You'll see the prompt:
```
nexusagent=>
```

### Useful psql commands (start with backslash)

| Command | What it does |
|---|---|
| `\dt` | List all tables |
| `\d nexus_contacts` | Describe a table — columns, types, indexes, constraints |
| `\du` | List all users (roles) |
| `\l` | List all databases |
| `\dn` | List schemas |
| `\df` | List functions |
| `\timing on` | Show how long each query takes |
| `\x` | Toggle expanded display (good for wide rows) |
| `\copy table TO 'file.csv' CSV HEADER` | Export to CSV |
| `\copy table FROM 'file.csv' CSV HEADER` | Import from CSV |
| `\? ` | Show all psql commands |
| `\q` | Quit |

### Sample SQL for NexusAgent

```sql
-- How many contacts per business?
SELECT business_id, COUNT(*) FROM nexus_contacts GROUP BY business_id;

-- Last 10 cloud calls
SELECT ts, provider, model, tokens_in, tokens_out, est_cost_usd
FROM nexus_cloud_usage ORDER BY id DESC LIMIT 10;

-- Anyone close to the daily token cap?
SELECT business_id, SUM(tokens_in + tokens_out) AS today_tokens
FROM nexus_cloud_usage
WHERE date = CURRENT_DATE::text
GROUP BY business_id
HAVING SUM(tokens_in + tokens_out) > 800000;

-- Audit log — who did what in the last hour
SELECT timestamp, tool_name, input_summary, success
FROM nexus_audit_log
WHERE timestamp > (NOW() - INTERVAL '1 hour')::text
ORDER BY timestamp DESC;
```

### Tip: save common queries as a `.sql` file

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U nexus -h localhost -p 5434 -d nexusagent -f my_queries.sql
```

---

## Option 3 — DBeaver / VS Code SQLTools (modern UI)

If pgAdmin feels heavy, a lighter modern UI:

### DBeaver Community (free, all OSes)

1. Download from https://dbeaver.io/download/
2. Install → New Connection → choose PostgreSQL
3. Host: `localhost`, Port: `5434`, Database: `nexusagent`, User: `nexus`, Password: `nexuspw`
4. Click **Test Connection**, then **Finish**

DBeaver is faster than pgAdmin for casual browsing, has prettier ERD diagrams, and supports many other databases — same UI for everything.

### VS Code extension: SQLTools + PostgreSQL driver

1. Install the **SQLTools** extension
2. Install **SQLTools PostgreSQL/Cockroach Driver**
3. Click the SQLTools icon in the activity bar → **Add New Connection** → PostgreSQL
4. Same connection details as above
5. Now you can run SQL inside VS Code, results appear inline

Best if you already live in VS Code and don't want to switch windows.

---

## Switching the app to use Postgres

You're not done yet just by setting up Postgres — the app currently uses SQLite by default. To make NexusAgent actually write to Postgres:

1. Stop the API server.
2. Edit `.env`:
   ```
   # Uncomment this line:
   DATABASE_URL=postgresql://nexus:nexuspw@localhost:5434/nexusagent
   ```
3. (First time only) **Migrate existing SQLite data into Postgres**:
   ```powershell
   $env:DATABASE_URL = "postgresql://nexus:nexuspw@localhost:5434/nexusagent"
   & "C:\Users\Praneeth p\OneDrive\Desktop\NexusAgent\venv\Scripts\python.exe" tools\migrate_to_postgres.py --dry-run
   ```
   Review the output — every table from SQLite should be listed. If it looks right, run again **without** `--dry-run`:
   ```powershell
   & "C:\Users\Praneeth p\OneDrive\Desktop\NexusAgent\venv\Scripts\python.exe" tools\migrate_to_postgres.py
   ```
4. Restart the API server. It now talks to Postgres.

To switch back to SQLite: comment out `DATABASE_URL` in `.env` and restart. Your SQLite file (`data/nexusagent.db`) is untouched.

---

## What lives where

After migration, here's where data goes:

| Data | Storage | Why |
|---|---|---|
| All app tables (CRM, tasks, invoices, agents, audit log, conversations, WhatsApp, cloud usage, etc.) | **Postgres** if `DATABASE_URL` set, else **SQLite** | The whole app routes through `config.db.get_conn()` |
| Document embeddings + RAG vectors | **ChromaDB** (`chroma_db/` folder) | Vector store, separate from SQL |
| Generated reports (PDFs, Excel) | **`outputs/`** folder | Files, not DB |
| Audit log (cloud LLM calls) | `outputs/cloud_audit.jsonl` + `nexus_audit_log` table | Both: file for tamper-evident, DB for queryable |
| `.jwt_secret` / `.nexus_smtp_secret` | `data/` folder | Symmetric keys — file-based |
| Whisper / Ollama models | `~/.ollama/` | Outside the project |

ChromaDB stays separate from Postgres — it's a vector database, not relational. NexusAgent uses both: Postgres/SQLite for structured records, ChromaDB for document embeddings.

---

## Common tasks

### "Show me how much I've spent on Bedrock today"
```sql
SELECT SUM(est_cost_usd) FROM nexus_cloud_usage WHERE date = CURRENT_DATE::text;
```

### "What businesses exist?"
```sql
SELECT id, name, created_at FROM nexus_businesses ORDER BY created_at;
```

### "Reset a business to empty (test cleanup)"
```sql
-- Be careful — this deletes data. Only use on test workspaces.
DELETE FROM nexus_contacts  WHERE business_id = 'biz-test';
DELETE FROM nexus_companies WHERE business_id = 'biz-test';
DELETE FROM nexus_deals     WHERE business_id = 'biz-test';
-- ... and so on for whatever tables you care about
```

### "Reset the cloud-budget counter for today"
```sql
DELETE FROM nexus_cloud_usage WHERE date = CURRENT_DATE::text;
```

### "Find which contacts are missing emails"
```sql
SELECT id, first_name, last_name FROM nexus_contacts
WHERE business_id = 'biz-a' AND (email IS NULL OR email = '');
```

### "Backup the whole database to a file"

```powershell
$env:PGPASSWORD = "nexuspw"
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U nexus -h localhost -p 5434 -d nexusagent -F c -f nexusagent_backup.dump
```

### "Restore from a backup"

```powershell
$env:PGPASSWORD = "nexuspw"
& "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -U nexus -h localhost -p 5434 -d nexusagent -c nexusagent_backup.dump
```

`-c` drops existing tables first. Without it the restore appends.

---

## Safety tips

- **Always `WHERE` your DELETEs and UPDATEs.** A bare `DELETE FROM nexus_contacts;` wipes the whole table. pgAdmin will warn you, but psql won't.
- **Wrap risky changes in a transaction** so you can roll back:
  ```sql
  BEGIN;
  DELETE FROM nexus_contacts WHERE business_id = 'biz-test';
  -- check the count looks right
  SELECT COUNT(*) FROM nexus_contacts;
  -- If wrong:
  ROLLBACK;
  -- If right:
  COMMIT;
  ```
- **Read-only mode for psql**: connect with `--set=transaction_isolation=READ_ONLY`. Even a fat-fingered DELETE will fail.
- **Keep daily backups**: schedule the `pg_dump` command above as a Windows Task. Even on local, even pre-launch.

---

## When something goes wrong

| Problem | Fix |
|---|---|
| `connection refused` from psql | Postgres service not running. `Get-Service postgres*` to check. |
| `authentication failed` for nexus | Password got reset / forgotten. Re-run `scripts\fix_nexus_password.ps1` as admin. |
| pgAdmin shows no tables under `public` | App hasn't booted against Postgres yet — the tables are created lazily on first connection. Boot the API once with `DATABASE_URL` set. |
| App is slow after switching to Postgres | Postgres needs ANALYZE: `ANALYZE;` runs the query planner stats. Then queries get fast. |
| `relation "nexus_X" does not exist` | App-side `CREATE TABLE IF NOT EXISTS` hasn't run yet. Boot the API once or call the relevant endpoint to trigger schema creation. |
| You want to start over fresh | `DROP DATABASE nexusagent; CREATE DATABASE nexusagent OWNER nexus;` (run as `postgres` superuser). All data gone. |

---

## TL;DR

1. **Open pgAdmin 4** → register server (host `localhost`, port `5434`, db `nexusagent`, user `nexus`, password `nexuspw`)
2. **Tables → Right-click → View/Edit Data → All Rows** to browse
3. **Database → Query Tool** to run SQL
4. **F5** to execute
5. The app still uses SQLite by default — uncomment `DATABASE_URL` in `.env` to switch
