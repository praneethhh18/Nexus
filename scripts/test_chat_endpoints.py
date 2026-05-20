"""Test the chat-UI backend endpoints (no LLM, fast).

Covers everything the chat sidebar + top-buttons hit:
  - GET  /api/conversations          (sidebar list)
  - POST /api/conversations          (New chat button)
  - GET  /api/conversations/{id}     (load on click)
  - PATCH /api/conversations/{id}    (rename)
  - PATCH /api/conversations/{id}/sensitive  (lock to local LLM)
  - DELETE /api/conversations/{id}   (sidebar trash icon)
  - POST /api/export/markdown        (Export -> Markdown)
  - POST /api/export/pdf             (Export -> PDF)

Uses Python's in-process call (FastAPI TestClient) so we don't need a
running uvicorn. Verdict for each endpoint goes to stdout.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from api.server import app

# Resolve a test user + business + auth token.
import psycopg
url = None
with open(os.path.join(REPO_ROOT, ".env"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

conn = psycopg.connect(url)
cur = conn.cursor()
cur.execute("SELECT id, email FROM nexus_users WHERE email LIKE 'praneethhh%' ORDER BY created_at DESC LIMIT 1")
u = cur.fetchone()
cur.execute("""
    SELECT b.id FROM nexus_businesses b
    LEFT JOIN nexus_contacts c ON c.business_id = b.id
    WHERE b.owner_id = %s GROUP BY b.id ORDER BY COUNT(c.id) DESC LIMIT 1
""", (u[0],))
biz_id = cur.fetchone()[0]
conn.close()

# Mint an access token using the same path /api/auth/login uses.
from api.auth import create_access_token
token = create_access_token(u[0], u[1], "admin")
H = {"Authorization": f"Bearer {token}", "X-Business-Id": biz_id}
print(f"User:     {u[1]}")
print(f"Business: {biz_id}\n")

client = TestClient(app)
results = []


def go(label, method, path, **kwargs):
    fn = getattr(client, method)
    try:
        r = fn(path, headers=H, **kwargs)
        ok = 200 <= r.status_code < 300
        results.append((label, method.upper(), path, r.status_code, "PASS" if ok else "FAIL"))
        print(f"  {'PASS' if ok else 'FAIL'}  {method.upper():6} {path:40} -> {r.status_code}")
        return r
    except Exception as e:
        results.append((label, method.upper(), path, 0, f"ERR: {e}"))
        print(f"  ERROR {method.upper():6} {path:40} -> {e}")
        return None


# 1. List conversations
go("list conversations", "get", "/api/conversations")

# 2. Create a new conversation
r = go("create conversation", "post", "/api/conversations",
       json={"title": "Test conversation"})
conv_id = (r.json().get("conversation_id") if r and r.status_code < 300 else None) if r else None

if conv_id:
    # 3. Load it
    go("load conversation",   "get",    f"/api/conversations/{conv_id}")
    # 4. Rename it
    go("rename conversation", "patch",  f"/api/conversations/{conv_id}",
        json={"title": "Renamed test"})
    # 5. Toggle sensitive
    go("toggle sensitive",    "patch",  f"/api/conversations/{conv_id}/sensitive",
        json={"sensitive": True})
    go("toggle sensitive off","patch",  f"/api/conversations/{conv_id}/sensitive",
        json={"sensitive": False})
    # 6. Export markdown
    go("export markdown",     "post",   "/api/export/markdown",
        json={"conversation_id": conv_id})
    # 7. Export PDF
    go("export pdf",          "post",   "/api/export/pdf",
        json={"conversation_id": conv_id})
    # 8. Delete it (cleanup)
    go("delete conversation", "delete", f"/api/conversations/{conv_id}")
else:
    print("  SKIP load/rename/sensitive/export/delete — conversation create failed")


# ── Summary ──────────────────────────────────────────────────────────────
passed = sum(1 for _, _, _, _, v in results if v == "PASS")
print(f"\nTOTAL: {passed}/{len(results)} endpoints OK")
for r in results:
    if not r[4].startswith("PASS"):
        print(f"  FAIL  {r[1]} {r[2]} -> {r[3]} {r[4]}")
