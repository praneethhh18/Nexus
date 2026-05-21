"""Full NexusAgent module audit — hit every GET endpoint the frontend
actually calls. Reports PASS / MISSING / 5XX per module so we know
which pages will work in the demo.
"""
import os, sys
from typing import List, Tuple
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
from fastapi.testclient import TestClient
from api.server import app
import psycopg
from api.auth import create_access_token

with open(os.path.join(REPO_ROOT, ".env"), encoding="utf-8") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip().strip('"').strip("'"); break
conn = psycopg.connect(url); cur = conn.cursor()
cur.execute("SELECT id, email FROM nexus_users WHERE email LIKE 'praneethhh%' ORDER BY created_at DESC LIMIT 1")
u = cur.fetchone()
cur.execute("SELECT b.id FROM nexus_businesses b LEFT JOIN nexus_contacts c ON c.business_id=b.id "
            "WHERE b.owner_id=%s GROUP BY b.id ORDER BY COUNT(c.id) DESC LIMIT 1", (u[0],))
biz_id = cur.fetchone()[0]; conn.close()
token = create_access_token(u[0], u[1], "admin")
H = {"Authorization": f"Bearer {token}", "X-Business-Id": biz_id}
print(f"User:     {u[1]}\nBusiness: {biz_id}\n")
c = TestClient(app)

# Paths actually called by the frontend (grepped from services + pages).
# Only GET endpoints — POST/PATCH/DELETE need bodies + risk side effects.
TARGETS = [
    # ── Auth + Session ──
    ("Auth", "/api/auth/me"),
    ("Auth", "/api/auth/sessions"),
    ("Auth", "/api/auth/2fa/status"),
    # ── Business + Onboarding + Setup ──
    ("Business", "/api/businesses"),
    ("Onboarding", "/api/onboarding"),
    ("Onboarding", "/api/business/greetings"),
    ("Onboarding", "/api/notifications/prefs"),
    ("Onboarding", "/api/dashboard/industry-kpis"),
    ("Setup", "/api/setup/status"),
    # ── Billing ──
    ("Billing", "/api/billing/plans"),
    ("Billing", "/api/billing/subscription"),
    # ── Chat + Conversations ──
    ("Chat", "/api/conversations"),
    ("Chat", "/api/agent/tools"),
    # ── CRM ──
    ("CRM", "/api/crm/contacts"),
    ("CRM", "/api/crm/companies"),
    ("CRM", "/api/crm/deals"),
    ("CRM", "/api/crm/pipeline"),
    ("CRM", "/api/crm/interactions"),
    # ── Tasks + Invoices + Documents ──
    ("Tasks", "/api/tasks"),
    ("Invoices", "/api/invoices"),
    ("Documents", "/api/documents"),
    # ── Agents (built-in + custom) + Approvals ──
    ("Agents", "/api/agents/personas"),
    ("Agents", "/api/agents/activity"),
    ("Agents", "/api/agents/nudges"),
    ("Agents", "/api/agents/runs"),
    ("Agents", "/api/agents/schedule"),
    ("CustomAgents", "/api/custom-agents"),
    ("CustomAgents", "/api/custom-agents/templates"),
    ("Approvals", "/api/approvals"),
    ("Approvals", "/api/approvals/pending-count"),
    # ── Workflows ──
    ("Workflows", "/api/workflows"),
    ("Workflows", "/api/workflows/templates"),
    ("Workflows", "/api/workflows/node-types"),
    ("Workflows", "/api/workflows/scheduler/jobs"),
    # ── Briefing + Activity + Memory + Audit ──
    ("Briefing", "/api/briefing/latest"),
    ("Briefing", "/api/briefing/evening/latest"),
    ("Memory", "/api/memory"),
    ("Audit", "/api/audit"),
    ("Privacy", "/api/privacy/status"),
    ("Privacy", "/api/privacy/audit"),
    ("Privacy", "/api/privacy-bridge"),
    # ── Analytics + Admin Metrics ──
    ("Analytics", "/api/analytics/pipeline-velocity"),
    ("Analytics", "/api/analytics/revenue-forecast"),
    ("Analytics", "/api/analytics/agent-impact"),
    ("Analytics", "/api/analytics/churn-risk"),
    ("AdminMetrics", "/api/admin/metrics"),
    ("AdminMetrics", "/api/admin/metrics/tenant"),
    # ── Notifications + Tags + Suggestions + Saved Queries ──
    ("Notifications", "/api/notifications"),
    ("Tags", "/api/tags"),
    ("Saved", "/api/saved-queries"),
    # ── Integrations + Calendar + Email + WhatsApp + Voice ──
    ("Integrations", "/api/integrations"),
    ("Integrations", "/api/integrations/providers"),
    ("Calendar", "/api/calendar/status"),
    ("Email", "/api/email-templates"),
    ("Email", "/api/email-triage/account"),
    ("WhatsApp", "/api/whatsapp/account"),
    ("WhatsApp", "/api/whatsapp/tenant/status"),
    ("Voice", "/api/vox/usage"),
    ("Voice", "/api/vox/calls"),
    # ── Database + SQL ──
    ("Database", "/api/database/tables"),
    # ── Team ──
    ("Team", "/api/team/invites"),
    ("Team", "/api/team/activity"),
    # ── Intake + Search ──
    ("Intake", "/api/intake/keys"),
    ("Search", "/api/search?q=test"),
    # ── Admin ──
    ("Admin", "/api/admin/backup/info"),
    # ── System ──
    ("System", "/api/health"),
    ("System", "/api/stats"),
    ("System", "/api/settings"),
]

results: List[Tuple[str, str, int, str]] = []
counts = {"OK": 0, "MISS": 0, "5XX": 0, "OTHER": 0}
issues_by_module = {}

for module, path in TARGETS:
    try:
        r = c.get(path, headers=H)
        sc = r.status_code
    except Exception as e:
        sc = 0
        results.append((module, path, sc, f"EXC {type(e).__name__}"))
        counts["OTHER"] += 1
        issues_by_module.setdefault(module, []).append((path, sc, str(e)[:80]))
        continue
    if 200 <= sc < 300:
        results.append((module, path, sc, "OK")); counts["OK"] += 1
    elif sc == 404:
        results.append((module, path, sc, "MISS")); counts["MISS"] += 1
        issues_by_module.setdefault(module, []).append((path, sc, "route not wired"))
    elif sc >= 500:
        body = r.text[:120].replace("\n", " ")
        results.append((module, path, sc, f"5XX {body}")); counts["5XX"] += 1
        issues_by_module.setdefault(module, []).append((path, sc, body))
    else:
        results.append((module, path, sc, f"S{sc}")); counts["OTHER"] += 1
        issues_by_module.setdefault(module, []).append((path, sc, r.text[:80]))

print(f"{'Status':<5}  {'Module':<14}  Path")
print("-" * 90)
for module, path, sc, note in results:
    tag = "OK  " if 200 <= sc < 300 else ("MISS" if sc == 404 else "FAIL")
    print(f"{tag:<5}  {module:<14}  {sc:>4}  {path}")

print()
print(f"OK: {counts['OK']}/{len(TARGETS)}   MISSING(404): {counts['MISS']}   5XX: {counts['5XX']}   OTHER: {counts['OTHER']}")
print()
if issues_by_module:
    print("──── Modules with issues ────")
    for module, errs in issues_by_module.items():
        print(f"\n[{module}]")
        for p, s, m in errs:
            print(f"  {s}  {p}  - {m}")
