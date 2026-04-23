"""
One-shot migration from SQLite to Postgres.

Dumps every table in the SQLite database, creates an equivalent schema in
Postgres, and copies the data in batches.

Usage:
    1. Stop the NexusAgent API server (so SQLite isn't being written to)
    2. Ensure Postgres is reachable via DATABASE_URL
    3. Run:  python tools/migrate_to_postgres.py --dry-run    # preview
             python tools/migrate_to_postgres.py              # do it

What it does:
    • Reads schema from sqlite_master for every non-system table
    • Translates CREATE TABLE to Postgres (AUTOINCREMENT → BIGSERIAL, etc.)
    • Creates tables in Postgres (skips if already present)
    • Copies rows in batches of 500 using psycopg's executemany

What it does NOT do:
    • Foreign-key constraints aren't preserved (SQLite is loose about them)
    • Indexes beyond PK aren't migrated — re-create them manually if critical
    • Triggers, views — NexusAgent doesn't use any

After running, update .env:
    DATABASE_URL=postgresql://user:pass@host:5432/nexusagent
and restart the app. The modules that still use sqlite3 directly will keep
using SQLite unless you've switched them to config.db.get_conn() first.
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DB_PATH

SKIP_TABLES = {"sqlite_sequence", "sqlite_stat1"}
BATCH_SIZE = 500


def _translate_create(sql: str) -> str:
    """Convert a SQLite CREATE TABLE statement to Postgres-compatible SQL."""
    s = sql
    s = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "BIGSERIAL PRIMARY KEY", s, flags=re.IGNORECASE)
    # Postgres doesn't support "DEFAULT '{}'" for TEXT columns with braces ambiguously;
    # already fine for TEXT.
    # Strip SQLite's CHECK constraints that use type affinities differently
    s = re.sub(r"\s+COLLATE\s+\w+", "", s, flags=re.IGNORECASE)
    # SQLite `REAL` → Postgres `DOUBLE PRECISION`
    s = re.sub(r"\bREAL\b", "DOUBLE PRECISION", s, flags=re.IGNORECASE)
    # SQLite `BLOB` → Postgres `BYTEA`
    s = re.sub(r"\bBLOB\b", "BYTEA", s, flags=re.IGNORECASE)
    return s


def _sqlite_tables(conn: sqlite3.Connection) -> List[dict]:
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [{"name": r[0], "sql": r[1]} for r in rows if r[0] not in SKIP_TABLES]


def _columns(conn: sqlite3.Connection, table: str) -> List[str]:
    info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    return [r[1] for r in info]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Preview only; don't write to Postgres")
    p.add_argument("--drop", action="store_true", help="DROP each target table before recreating")
    args = p.parse_args()

    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn.startswith(("postgresql://", "postgres://")):
        print("❌ DATABASE_URL is not set to a Postgres URL.")
        print("   Example: postgresql://nexus:password@localhost:5432/nexusagent")
        sys.exit(2)

    src = Path(DB_PATH)
    if not src.exists():
        print(f"❌ SQLite database not found: {src}")
        sys.exit(2)

    try:
        import psycopg
    except ImportError:
        print("❌ psycopg not installed. Run: pip install 'psycopg[binary]>=3.1'")
        sys.exit(2)

    print(f"📦 Source:      {src}")
    print(f"🎯 Target:      {dsn.split('@')[-1] if '@' in dsn else dsn}")
    print(f"🔧 Dry run:     {args.dry_run}")
    print(f"🔧 Drop first:  {args.drop}")
    print()

    lite = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    lite.row_factory = sqlite3.Row
    tables = _sqlite_tables(lite)
    print(f"Found {len(tables)} tables:")
    for t in tables:
        print(f"  • {t['name']}")
    print()

    if args.dry_run:
        print("✅ Dry run complete. Re-run without --dry-run to execute.")
        return

    pg = psycopg.connect(dsn, autocommit=False)

    try:
        for t in tables:
            name = t["name"]
            print(f"→ {name}")
            cols = _columns(lite, name)
            if not cols:
                print(f"  (skipped — no columns)")
                continue

            # Create target table
            create_sql = _translate_create(t["sql"])
            with pg.cursor() as cur:
                if args.drop:
                    cur.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
                try:
                    cur.execute(create_sql)
                    pg.commit()
                except psycopg.Error as e:
                    pg.rollback()
                    if "already exists" in str(e).lower():
                        print(f"  (table exists — skipping create; use --drop to replace)")
                    else:
                        print(f"  ❌ CREATE failed: {e}")
                        print(f"     SQL: {create_sql[:200]}...")
                        continue

            # Copy rows in batches
            total = lite.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
            if total == 0:
                print(f"  (0 rows)")
                continue

            placeholders = ",".join(["%s"] * len(cols))
            col_list = ",".join(f'"{c}"' for c in cols)
            insert_sql = f'INSERT INTO "{name}" ({col_list}) VALUES ({placeholders})'

            copied = 0
            cursor = lite.execute(f"SELECT {','.join(f'[{c}]' for c in cols)} FROM [{name}]")
            batch = []
            with pg.cursor() as pcur:
                while True:
                    row = cursor.fetchone()
                    if row is None:
                        break
                    batch.append(tuple(row))
                    if len(batch) >= BATCH_SIZE:
                        pcur.executemany(insert_sql, batch)
                        copied += len(batch)
                        batch = []
                        print(f"  ...{copied}/{total}")
                if batch:
                    pcur.executemany(insert_sql, batch)
                    copied += len(batch)
            pg.commit()
            print(f"  ✅ Copied {copied}/{total}")

    finally:
        pg.close()
        lite.close()

    print()
    print("✅ Migration complete.")
    print("   Set DATABASE_URL in .env to point at Postgres, then switch each")
    print("   data module from 'sqlite3.connect(DB_PATH)' to 'config.db.get_conn()'.")


if __name__ == "__main__":
    main()
