"""One-off: nuke a user and all their data.

Run from repo root:
    python scripts/delete_user.py <email>

Discovers business-scoped and user-scoped tables by inspecting the DB
catalog. Operates on whichever DB has the user — checks SQLite first
(fast, file-local), falls back to Postgres if not found there.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from typing import List, Optional, Tuple


# Resolve repo paths without importing the project (so we don't pull in the
# psycopg pool side-effects that confused the previous run).
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SQLITE_PATH = os.path.join(REPO_ROOT, "data", "nexusagent.db")


def _wipe_sqlite(email: str) -> int:
    if not os.path.exists(SQLITE_PATH):
        print(f"  no sqlite db at {SQLITE_PATH}")
        return 1
    conn = sqlite3.connect(SQLITE_PATH)
    try:
        row = conn.execute(
            "SELECT id, email, name FROM nexus_users WHERE LOWER(email)=LOWER(?)",
            (email,),
        ).fetchone()
        if not row:
            print(f"  user not found in sqlite")
            return 1
        user_id = row[0]
        print(f"  SQLite hit: id={user_id} email={row[1]} name={row[2]}")

        owned = conn.execute(
            "SELECT id FROM nexus_businesses WHERE owner_id=?", (user_id,)
        ).fetchall()
        member = conn.execute(
            "SELECT business_id FROM nexus_business_members WHERE user_id=?", (user_id,)
        ).fetchall()
        biz_ids = sorted({r[0] for r in owned} | {r[0] for r in member})
        print(f"  businesses: {biz_ids}")

        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nexus_%'"
        ).fetchall()]
        biz_tables, usr_tables = [], []
        for t in tables:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})").fetchall()]
            if "business_id" in cols: biz_tables.append(t)
            if "user_id" in cols:     usr_tables.append(t)
        print(f"  business_id tables: {len(biz_tables)} | user_id tables: {len(usr_tables)}")

        deleted: dict[str, int] = {}
        for bid in biz_ids:
            for t in biz_tables:
                try:
                    cur = conn.execute(f"DELETE FROM {t} WHERE business_id=?", (bid,))
                    if cur.rowcount:
                        deleted[t] = deleted.get(t, 0) + cur.rowcount
                except Exception as e:
                    print(f"    skip {t}: {e}")
        for t in usr_tables:
            try:
                cur = conn.execute(f"DELETE FROM {t} WHERE user_id=?", (user_id,))
                if cur.rowcount:
                    deleted[t] = deleted.get(t, 0) + cur.rowcount
            except Exception as e:
                print(f"    skip {t}: {e}")
        for bid in biz_ids:
            cur = conn.execute("DELETE FROM nexus_businesses WHERE id=?", (bid,))
            if cur.rowcount:
                deleted["nexus_businesses"] = deleted.get("nexus_businesses", 0) + cur.rowcount
        cur = conn.execute("DELETE FROM nexus_users WHERE id=?", (user_id,))
        deleted["nexus_users"] = cur.rowcount or 0

        conn.commit()

        print("  deleted rows:")
        for t in sorted(deleted):
            print(f"    {t}: {deleted[t]}")
        return 0
    finally:
        conn.close()


def _wipe_postgres(email: str) -> int:
    url = os.getenv("DATABASE_URL")
    if not url:
        # Try .env
        env_path = os.path.join(REPO_ROOT, ".env")
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not url:
        print("  no DATABASE_URL")
        return 1
    try:
        import psycopg
    except ImportError:
        print("  psycopg not installed")
        return 1
    conn = psycopg.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name FROM nexus_users WHERE LOWER(email)=LOWER(%s)",
                (email,),
            )
            row = cur.fetchone()
            if not row:
                print(f"  user not found in postgres")
                return 1
            user_id = row[0]
            print(f"  Postgres hit: id={user_id} email={row[1]} name={row[2]}")

            cur.execute("SELECT id FROM nexus_businesses WHERE owner_id=%s", (user_id,))
            owned = cur.fetchall()
            cur.execute("SELECT business_id FROM nexus_business_members WHERE user_id=%s", (user_id,))
            member = cur.fetchall()
            biz_ids = sorted({r[0] for r in owned} | {r[0] for r in member})
            print(f"  businesses: {biz_ids}")

            cur.execute(
                "SELECT table_name FROM information_schema.columns "
                "WHERE table_schema='public' AND column_name=%s AND table_name LIKE 'nexus_%%'",
                ("business_id",),
            )
            biz_tables = [r[0] for r in cur.fetchall()]
            cur.execute(
                "SELECT table_name FROM information_schema.columns "
                "WHERE table_schema='public' AND column_name=%s AND table_name LIKE 'nexus_%%'",
                ("user_id",),
            )
            usr_tables = [r[0] for r in cur.fetchall()]
            print(f"  business_id tables: {len(biz_tables)} | user_id tables: {len(usr_tables)}")

            deleted: dict[str, int] = {}
            for bid in biz_ids:
                for t in biz_tables:
                    try:
                        cur.execute(f'DELETE FROM "{t}" WHERE business_id=%s', (bid,))
                        if cur.rowcount:
                            deleted[t] = deleted.get(t, 0) + cur.rowcount
                    except Exception as e:
                        conn.rollback()
                        print(f"    skip {t}: {e}")
            for t in usr_tables:
                try:
                    cur.execute(f'DELETE FROM "{t}" WHERE user_id=%s', (user_id,))
                    if cur.rowcount:
                        deleted[t] = deleted.get(t, 0) + cur.rowcount
                except Exception as e:
                    conn.rollback()
                    print(f"    skip {t}: {e}")
            for bid in biz_ids:
                cur.execute("DELETE FROM nexus_businesses WHERE id=%s", (bid,))
                if cur.rowcount:
                    deleted["nexus_businesses"] = deleted.get("nexus_businesses", 0) + cur.rowcount
            cur.execute("DELETE FROM nexus_users WHERE id=%s", (user_id,))
            deleted["nexus_users"] = cur.rowcount or 0

        conn.commit()
        print("  deleted rows:")
        for t in sorted(deleted):
            print(f"    {t}: {deleted[t]}")
        return 0
    finally:
        conn.close()


def main(email: str) -> int:
    print(f"Looking for {email!r}")
    print("--- SQLite ---")
    sqlite_rc = _wipe_sqlite(email)
    print("--- Postgres ---")
    pg_rc = _wipe_postgres(email)
    if sqlite_rc == 0 or pg_rc == 0:
        print(f"\nDone. {email} can re-register.")
        return 0
    print(f"\nUser not found in either DB.")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python scripts/delete_user.py <email>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
