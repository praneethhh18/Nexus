"""Test all 8 slash commands via the rewrites the frontend uses.

The frontend rewrites /remind, /task, /deal, /contact, /invoice, /brief,
/triage, /whatif → natural language, then runs them through the same
agent path as a typed message. So we hit run_agent with those rewrites
and assert each one calls the right tool (or, for /whatif, that the
endpoint returns a structured before/after dict).

Speed-wise this is the same shape as test_chat_full.py — same per-test
60s timeout, same business + user resolution, same flush-as-we-go
output. Lives in its own file so we can iterate on slash UX without
re-running the big LLM-quality suite.
"""
from __future__ import annotations

import os, sys, time, json, concurrent.futures
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

RESULT_PATH = os.path.join(REPO_ROOT, "scripts", "_test_slash_results.log")
PER_TEST_TIMEOUT = 60


def _resolve_user() -> Dict[str, str]:
    import psycopg
    url = None
    with open(os.path.join(REPO_ROOT, ".env"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    conn = psycopg.connect(url)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, role FROM nexus_users "
                    "WHERE email LIKE 'praneethhh%' ORDER BY created_at DESC LIMIT 1")
        u = cur.fetchone()
        cur.execute("""
            SELECT b.id, b.name FROM nexus_businesses b
            LEFT JOIN nexus_contacts c ON c.business_id = b.id
            WHERE b.owner_id = %s GROUP BY b.id, b.name
            ORDER BY COUNT(c.id) DESC, b.created_at DESC LIMIT 1
        """, (u[0],))
        b = cur.fetchone()
        return {"user_id": u[0], "user_email": u[1], "user_name": u[2],
                "user_role": u[3] or "owner",
                "business_id": b[0], "business_name": b[1]}
    finally:
        conn.close()


CTX = _resolve_user()
print(f"User:     {CTX['user_name']} ({CTX['user_email']})")
print(f"Business: {CTX['business_name']} ({CTX['business_id']})\n")


def _run_agent(prompt: str) -> Dict[str, Any]:
    t0 = time.time()
    out: Dict[str, Any] = {"prompt": prompt, "tools": [], "answer": "",
                           "warnings": [], "elapsed_ms": 0, "error": None}
    try:
        from agents.agent_loop import run_agent
        result = run_agent(
            messages=[{"role": "user", "content": prompt}],
            business_id=CTX["business_id"], business_name=CTX["business_name"],
            user_id=CTX["user_id"], user_name=CTX["user_name"],
            user_role=CTX["user_role"],
        )
        out["answer"] = (result.get("answer") or "")[:300]
        out["tools"] = [tc.get("name") for tc in result.get("tool_calls", [])]
        out["warnings"] = result.get("grounding_warnings", [])
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out


def _run(prompt: str) -> Dict[str, Any]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        f = pool.submit(_run_agent, prompt)
        try:
            return f.result(timeout=PER_TEST_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return {"prompt": prompt, "tools": [], "answer": "", "warnings": [],
                    "elapsed_ms": PER_TEST_TIMEOUT * 1000,
                    "error": f"hung > {PER_TEST_TIMEOUT}s"}


def _run_whatif() -> Dict[str, Any]:
    """The /whatif slash command bypasses the agent — it calls api.simulator
    directly via what_if() and renders the structured response. Mirror that
    here so we exercise the same code path as the chat UI."""
    t0 = time.time()
    out: Dict[str, Any] = {"prompt": "/whatif revenue drops 10%", "tools": [],
                           "answer": "", "warnings": [], "elapsed_ms": 0,
                           "error": None}
    try:
        from utils.whatif_simulator import run_full_simulation
        r = run_full_simulation("revenue drops 10%", business_id=CTX["business_id"])
        if isinstance(r, dict) and ("before_total_revenue" in r or "error" in r):
            out["answer"] = json.dumps({k: v for k, v in r.items()
                                       if k not in ("before_df", "after_df")})[:300]
        else:
            out["error"] = f"unexpected shape: {type(r).__name__}"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out


# The 8 slash commands the chat UI ships. We verify the agent reaches the
# right tool for each, mirroring the SLASH_COMMANDS rewrite map in Chat.jsx.
TESTS: List[Tuple[str, str, str, Callable]] = [
    ("/task",    "/task Call Meera Iyer at 4pm",
        "Create a task: Call Meera Iyer at 4pm.",
        lambda r: ("create_task" in r["tools"], f"tools={r['tools']}")),
    ("/contact", "/contact Test Contact From Slash",
        "Add a contact named Test Contact From Slash to the CRM.",
        lambda r: ("create_contact" in r["tools"], f"tools={r['tools']}")),
    ("/deal",    "/deal Q3 Pilot Onboarding",
        'Create a deal called "Q3 Pilot Onboarding" at the lead stage.',
        lambda r: ("create_deal" in r["tools"], f"tools={r['tools']}")),
    ("/remind",  "/remind",
        "Draft an invoice reminder email for the most overdue invoice.",
        # Either find_invoices+send_email or just send_email is OK — we
        # just need to confirm the agent goes to the email pipeline.
        lambda r: (any(t in r["tools"] for t in ("send_email", "find_invoices", "list_invoices")),
                   f"tools={r['tools']}")),
    ("/invoice", "/invoice Praneeth P K 5000",
        "Draft an invoice for Praneeth P K 5000.",
        # Draft an invoice triggers create_invoice or find_contacts→create_invoice.
        lambda r: (any(t in r["tools"] for t in ("create_invoice", "find_contacts")),
                   f"tools={r['tools']}")),
    ("/brief",   "/brief",
        "Generate today's morning briefing.",
        # Morning briefing can use a tool or be assembled by the agent;
        # accept either an answer with substantive content or a relevant tool.
        lambda r: ((len(r["answer"] or "") > 50 or any("briefing" in (t or "").lower() for t in r["tools"])),
                   f"answer too short / no briefing tool — tools={r['tools']}")),
    ("/triage",  "/triage",
        "Run email triage on the inbox now.",
        lambda r: ("triage_inbox" in r["tools"], f"tools={r['tools']}")),
    ("/whatif",  "/whatif revenue drops 10%",
        "(inline — calls utils.whatif_simulator.run_full_simulation)",
        lambda r: ((not r.get("error")) and ("before_total_revenue" in (r.get("answer") or "")),
                   f"answer={r.get('answer','')[:100]} err={r.get('error')}")),
]


results: List[Dict[str, Any]] = []


def _flush() -> None:
    with open(RESULT_PATH, "w", encoding="utf-8") as fh:
        fh.write(f"User:     {CTX['user_name']} ({CTX['user_email']})\n")
        fh.write(f"Business: {CTX['business_name']} ({CTX['business_id']})\n\n")
        for i, r in enumerate(results, 1):
            tag = "PASS" if r["pass"] else "FAIL"
            fh.write(f"[{i}] {tag}  {r['name']}\n")
            fh.write(f"     prompt:  {r['rewrite']}\n")
            fh.write(f"     tools:   {r.get('tools')}\n")
            fh.write(f"     elapsed: {r['elapsed_ms']}ms\n")
            fh.write(f"     reason:  {r['reason']}\n")
            if r.get("error"):
                fh.write(f"     ERROR:   {r['error']}\n")
            fh.write(f"     answer:  {(r['answer'] or '')[:200]}\n\n")
        passed = sum(1 for r in results if r["pass"])
        fh.write(f"\nTOTAL: {passed}/{len(results)} slash commands OK\n")


for i, (name, displayed, rewrite, check) in enumerate(TESTS, 1):
    print(f"[{i}/{len(TESTS)}] {name}: {displayed}", flush=True)
    r = _run_whatif() if name == "/whatif" else _run(rewrite)
    r["name"] = name
    r["rewrite"] = rewrite
    if r.get("error") and "/whatif" not in name:
        passed, reason = False, f"ERROR — {r['error']}"
    else:
        ok, why = check(r)
        passed, reason = ok, why if not ok else ""
    r["pass"] = bool(passed)
    r["reason"] = reason or ""
    print(f"     {'PASS' if passed else 'FAIL'}    ({r['elapsed_ms']}ms){'  '+reason if reason else ''}\n",
          flush=True)
    results.append(r)
    _flush()


passed = sum(1 for r in results if r["pass"])
print(f"\nTOTAL: {passed}/{len(results)} slash commands OK")
print(f"Detailed log: {RESULT_PATH}")
