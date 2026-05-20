"""Fix Postgres sequences that got out of sync with their tables.

Symptom: INSERT fails with
  duplicate key value violates unique constraint "..._pkey"
  DETAIL: Key (id)=(N) already exists.

Cause: data was loaded with explicit IDs (e.g., during a SQLite -> Postgres
migration) and the SERIAL sequence wasn't bumped to match. Postgres then
hands out an already-used number on the next INSERT.

Run from repo root:
    python scripts/fix_pg_sequences.py
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Tables known to have a serial id that may need bumping.
# Add more as we discover them.
TARGETS = [
    ("nexus_conversation_messages", "id"),
]


def _load_url() -> str | None:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    env_path = os.path.join(REPO_ROOT, ".env")
    if not os.path.exists(env_path):
        return None
    with open(env_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def main() -> int:
    url = _load_url()
    if not url:
        print("No DATABASE_URL — nothing to do.")
        return 1
    try:
        import psycopg
    except ImportError:
        print("psycopg not installed")
        return 1

    conn = psycopg.connect(url)
    fixed = 0
    try:
        with conn.cursor() as cur:
            for table, col in TARGETS:
                cur.execute(
                    f"SELECT pg_get_serial_sequence(%s, %s)",
                    (table, col),
                )
                seq_row = cur.fetchone()
                seq = seq_row[0] if seq_row else None
                if not seq:
                    print(f"  {table}.{col}: no serial sequence (skip)")
                    continue
                cur.execute(f'SELECT COALESCE(MAX("{col}"), 0) FROM "{table}"')
                max_id = cur.fetchone()[0] or 0
                cur.execute(f"SELECT last_value FROM {seq}")
                last_val = cur.fetchone()[0]
                target = max(max_id, 1)
                if last_val >= target and max_id > 0:
                    print(f"  {table}.{col}: seq={last_val} >= max_id={max_id} (already fine)")
                    continue
                cur.execute(f"SELECT setval(%s, %s, true)", (seq, target))
                print(f"  {table}.{col}: bumped seq {last_val} -> {target} (max_id={max_id})")
                fixed += 1
        conn.commit()
    finally:
        conn.close()

    print(f"\nFixed {fixed} sequence(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
