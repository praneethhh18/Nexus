"""
One-shot SQLite → config.db.get_conn() rewrite for files with the standard
pattern. Skips files that have unusual structures — those need manual edits.

Pattern:
  Before:
    import sqlite3
    from pathlib import Path
    ...
    from config.settings import DB_PATH
    ...
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

  After:
    import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
    ...
    from config.db import get_conn
    ...
    conn = get_conn()

The script does NOT touch:
  - INSERT OR REPLACE / INSERT OR IGNORE  (callers must rewrite themselves)
  - lastrowid                              (callers must use RETURNING)
  - PRAGMA table_info migration helpers    (callers must use try/except ALTER)

It just handles the boring imports + connection swap.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    # Phase D, E, F, G — agents, routers, sql, workflows, misc
    "agents/personas.py",
    "agents/summarizer.py",
    "agents/briefing.py",
    "agents/nudges.py",
    "agents/email_triage.py",
    "agents/approval_queue.py",
    "agents/background/scheduler.py",
    "agents/background/invoice_reminder.py",
    "agents/background/stale_deal_watcher.py",
    "agents/background/meeting_prep.py",
    "api/routers/lead_scoring.py",
    "api/routers/email_paste.py",
    "api/routers/backup.py",
    "api/routers/forge.py",
    "api/routers/bant.py",
    "api/routers/intake.py",
    "api/routers/database.py",
    "api/routers/notifications.py",
    "api/routers/errors.py",
    "api/db_indexes.py",
    "api/invoices.py",
    "api/tasks.py",
    "sql_agent/data_import.py",
    "sql_agent/executor.py",
    "sql_agent/db_setup.py",
    "sql_agent/schema_reader.py",
    "workflows/scheduler.py",
    "utils/whatif_simulator.py",
    "memory/audit_logger.py",
    "orchestrator/proactive_monitor.py",
]


def migrate_file(p: Path) -> tuple[bool, str]:
    """Apply the migration to one file. Returns (changed, summary)."""
    text = p.read_text(encoding="utf-8")
    original = text
    changes = []

    # 1. Replace the import line.
    if "from config.settings import DB_PATH\n" in text:
        text = text.replace(
            "from config.settings import DB_PATH\n",
            "from config.db import get_conn\n",
        )
        changes.append("import")
    elif re.search(r"^from config\.settings import DB_PATH$", text, re.MULTILINE):
        # No trailing newline match — handle that edge case
        text = re.sub(
            r"^from config\.settings import DB_PATH$",
            "from config.db import get_conn",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        changes.append("import")

    # 2. Tag the sqlite3 import for clarity.
    text = re.sub(
        r"^import sqlite3$",
        "import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db",
        text,
        count=1,
        flags=re.MULTILINE,
    )

    # 3. Drop the parent.mkdir line (config.db handles it for SQLite, no-op for Postgres).
    new_text, n = re.subn(
        r"\s*Path\(DB_PATH\)\.parent\.mkdir\(parents=True, exist_ok=True\)\n",
        "\n",
        text,
    )
    if n:
        text = new_text
        changes.append(f"mkdir×{n}")

    # 4. Replace sqlite3.connect(DB_PATH) with get_conn().
    new_text, n = re.subn(r"sqlite3\.connect\(DB_PATH\)", "get_conn()", text)
    if n:
        text = new_text
        changes.append(f"connect×{n}")

    # 5. Drop annotation `-> sqlite3.Connection` on _conn / _get_conn / etc
    #    since the wrapper isn't a sqlite3.Connection but is API-compatible.
    text = re.sub(r" -> sqlite3\.Connection:", ":", text)

    if text == original:
        return False, "no changes"
    p.write_text(text, encoding="utf-8")
    return True, ", ".join(changes)


def main():
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            print(f"  SKIP (missing): {rel}")
            continue
        changed, summary = migrate_file(p)
        flag = "[OK]" if changed else "[--]"
        print(f"  {flag} {rel:<40} {summary}")


if __name__ == "__main__":
    main()
