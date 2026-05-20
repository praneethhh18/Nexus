"""Kill Postgres backends that have been stuck for over 5 minutes.

The trigger: hot-reload uvicorn restarts left a chain of CREATE INDEX
statements waiting on an 'idle in transaction' email-triage session,
cascading into a 18-connection deadlock that prevents the server from
booting. This script clears that backlog so the next restart works.

Safety:
  - Only kills connections to the current database.
  - Only kills connections in state 'active' (with a CREATE INDEX in
    flight) or 'idle in transaction' (the original culprit).
  - Skips its OWN pid so the script doesn't kill itself.
  - Skips connections younger than 5 minutes — protects fresh work.
"""
import os, psycopg

url = None
with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

conn = psycopg.connect(url)
conn.autocommit = True
cur = conn.cursor()

cur.execute(
    "SELECT pid, state, NOW() - state_change AS age, substring(coalesce(query,''), 1, 60) "
    "FROM pg_stat_activity "
    "WHERE datname = current_database() "
    "  AND pid <> pg_backend_pid() "
    "  AND state IN ('active', 'idle in transaction') "
    "  AND NOW() - state_change > INTERVAL '5 minutes' "
    "ORDER BY age DESC"
)
victims = cur.fetchall()
print(f"Found {len(victims)} stuck backends to terminate:")
for v in victims:
    print(f"  pid={v[0]} state={v[1]} age={v[2]} q={v[3]!r}")

killed = 0
for v in victims:
    pid = v[0]
    try:
        cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
        ok = cur.fetchone()[0]
        if ok:
            killed += 1
            print(f"  killed pid {pid}")
        else:
            print(f"  could not kill pid {pid} (may have already died)")
    except Exception as e:
        print(f"  error killing pid {pid}: {e}")

print(f"\nDone. {killed}/{len(victims)} terminated.")
conn.close()
