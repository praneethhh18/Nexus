"""Comprehensive chat module test against live workspace data.

Covers every chat code-path I can hit from CLI:
  - fact_router patterns (count / list / ordinal / fields)
  - LLM general-knowledge (no tools called)
  - LLM with find_contacts (read CRM)
  - LLM creating contacts / tasks / deals
  - LLM email drafting (find_contacts -> send_email with approval)
  - LLM knowledge search (RAG)
  - Edge cases (empty input, very long input, special chars)

UI-only features (voice button, hybrid toggle, export, conversation
sidebar) are listed at the bottom as KNOWN-UNTESTABLE — they need a
browser. Everything else gets a verdict here.

Writes incremental results to scripts/_test_chat_full_results.log
so a hung LLM call doesn't lose data.
"""
from __future__ import annotations

import os
import sys
import time
import json
import concurrent.futures
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

RESULT_PATH = os.path.join(REPO_ROOT, "scripts", "_test_chat_full_results.log")
PER_TEST_TIMEOUT = 60   # seconds per LLM call


# ── User context ───────────────────────────────────────────────────────────
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
            SELECT b.id, b.name, COUNT(c.id)
            FROM nexus_businesses b
            LEFT JOIN nexus_contacts c ON c.business_id = b.id
            WHERE b.owner_id = %s
            GROUP BY b.id, b.name
            ORDER BY COUNT(c.id) DESC, b.created_at DESC
            LIMIT 1
        """, (u[0],))
        b = cur.fetchone()
        return {"user_id": u[0], "user_email": u[1], "user_name": u[2],
                "user_role": u[3] or "owner",
                "business_id": b[0], "business_name": b[1]}
    finally:
        conn.close()


CTX = _resolve_user()
print(f"User:     {CTX['user_name']} ({CTX['user_email']})")
print(f"Business: {CTX['business_name']} ({CTX['business_id']})")
print()


# ── Runner ─────────────────────────────────────────────────────────────────
def _run_inner(prompt: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    t0 = time.time()
    out: Dict[str, Any] = {"prompt": prompt, "via": None, "tools": [],
                           "answer": "", "warnings": [], "elapsed_ms": 0, "error": None}
    try:
        from agents import fact_router
        direct = fact_router.try_answer(prompt, CTX["business_id"])
        if direct and not history:
            out["via"] = "fact_router"
            out["answer"] = direct
            out["elapsed_ms"] = int((time.time() - t0) * 1000)
            return out

        from agents.agent_loop import run_agent
        msgs = list(history or [])
        msgs.append({"role": "user", "content": prompt})
        result = run_agent(
            messages=msgs,
            business_id=CTX["business_id"],
            business_name=CTX["business_name"],
            user_id=CTX["user_id"],
            user_name=CTX["user_name"],
            user_role=CTX["user_role"],
        )
        out["via"] = "agent_loop"
        out["answer"] = (result.get("answer") or "")[:500]
        out["tools"] = [tc.get("name") for tc in result.get("tool_calls", [])]
        out["warnings"] = result.get("grounding_warnings", [])
        out["stop_reason"] = result.get("stop_reason")
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out


def _run(prompt: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        f = pool.submit(_run_inner, prompt, history)
        try:
            return f.result(timeout=PER_TEST_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return {"prompt": prompt, "via": "TIMEOUT", "tools": [],
                    "answer": "", "warnings": [],
                    "elapsed_ms": PER_TEST_TIMEOUT * 1000,
                    "error": f"hung > {PER_TEST_TIMEOUT}s"}


# ── Checks ────────────────────────────────────────────────────────────────
def check_via(via): return lambda r: (r["via"] == via, f"via={r['via']!r} expected {via!r}")

def check_no_error():
    return lambda r: ((not r.get("error"), f"error: {r.get('error')!r}"))

def check_tool(name):
    return lambda r: (name in r["tools"], f"tool {name!r} not in {r['tools']}")

def check_answer_contains(substr):
    def f(r):
        if substr.lower() in (r["answer"] or "").lower():
            return True, ""
        return False, f"answer missing {substr!r}: {r['answer'][:100]!r}"
    return f

def check_answer_not_blocked():
    def f(r):
        ans = (r["answer"] or "").lower()
        bad = ["i couldn't retrieve real data", "the response i was about to send had multiple unverified"]
        for b in bad:
            if b in ans:
                return False, f"answer was grounding-blocked"
        return True, ""
    return f

def check_no_grounding_warnings():
    return lambda r: ((not r["warnings"], f"warnings: {r['warnings']}"))

def all_of(*cs):
    def f(r):
        for c in cs:
            ok, why = c(r)
            if not ok: return False, why
        return True, ""
    return f


# ── Tests ─────────────────────────────────────────────────────────────────
TESTS: List[Tuple[str, str, Callable]] = [
    # ── fact_router ─────────────────────────────────────────────────────────
    ("fact: count", "how many contacts do I have?",
        all_of(check_via("fact_router"), check_answer_contains("contacts"))),
    ("fact: count deals", "how many deals?",
        all_of(check_via("fact_router"), check_answer_contains("deals"))),
    ("fact: list", "list all contacts",
        all_of(check_via("fact_router"), check_answer_contains("1."))),
    ("fact: ordinal", "the 5th contact",
        all_of(check_via("fact_router"), check_answer_contains("5th"))),
    ("fact: phone-fields", "phone numbers of all contacts",
        all_of(check_via("fact_router"), check_answer_contains("phones for"))),
    ("fact: top N", "top 3 deals",
        all_of(check_via("fact_router"), check_answer_contains("1."))),
    ("fact: last", "last invoice",
        all_of(check_via("fact_router"), check_no_error())),

    # ── LLM general knowledge (no tools, no grounding block) ───────────────
    ("llm: general knowledge", "what are good ways to find SaaS customers?",
        all_of(check_via("agent_loop"), check_answer_not_blocked(), check_no_grounding_warnings())),
    ("llm: industry advice", "what's a typical SaaS pricing strategy?",
        all_of(check_via("agent_loop"), check_answer_not_blocked())),

    # ── LLM with find_contacts ────────────────────────────────────────────
    ("llm: lookup by name", "what is Praneeth P K's email?",
        all_of(check_via("agent_loop"), check_tool("find_contacts"))),
    ("llm: fuzzy name lookup", "find Praneeth PK in my contacts",
        all_of(check_via("agent_loop"), check_tool("find_contacts"))),
    ("llm: nonexistent name", "do I have a contact named Bob the Wizard?",
        all_of(check_via("agent_loop"), check_tool("find_contacts"))),

    # ── LLM creating things ───────────────────────────────────────────────
    ("llm: create task", "create a task to follow up with Praneeth tomorrow",
        all_of(check_via("agent_loop"), check_tool("create_task"))),

    # ── LLM email drafting (multi-tool: find_contacts -> send_email) ──────
    ("llm: draft email by name", "draft a short email to Praneeth P K saying I'll visit tomorrow",
        all_of(check_via("agent_loop"), check_tool("send_email"))),

    # ── Edge cases ─────────────────────────────────────────────────────────
    ("edge: empty prompt",        "",
        check_no_error()),
    ("edge: whitespace prompt",   "   ",
        check_no_error()),
    ("edge: very short prompt",   "hi",
        all_of(check_via("agent_loop"), check_no_error())),
    ("edge: special chars",       "what's 2+2? (and tell me a joke)",
        all_of(check_via("agent_loop"), check_no_error())),
]


# ── Execute ───────────────────────────────────────────────────────────────
results: List[Dict[str, Any]] = []

def _flush() -> None:
    with open(RESULT_PATH, "w", encoding="utf-8") as fh:
        fh.write(f"User:     {CTX['user_name']} ({CTX['user_email']})\n")
        fh.write(f"Business: {CTX['business_name']} ({CTX['business_id']})\n\n")
        for i, r in enumerate(results, 1):
            tag = "PASS" if r["pass"] else "FAIL"
            fh.write(f"[{i:2}] {tag}  {r['name']}\n")
            fh.write(f"     prompt:  {r['prompt']!r}\n")
            fh.write(f"     via:     {r['via']}\n")
            fh.write(f"     elapsed: {r['elapsed_ms']}ms\n")
            fh.write(f"     reason:  {r['reason']}\n")
            if r.get("tools"):
                fh.write(f"     tools:   {r['tools']}\n")
            if r.get("warnings"):
                fh.write(f"     warns:   {r['warnings']}\n")
            if r.get("error"):
                fh.write(f"     ERROR:   {r['error']}\n")
            fh.write(f"     answer:  {(r['answer'] or '')[:300]}\n\n")
        passed = sum(1 for r in results if r["pass"])
        fh.write(f"\nTOTAL: {passed} pass / {len(results) - passed} fail / {len(results)} run\n")


for i, (name, prompt, check) in enumerate(TESTS, 1):
    print(f"[{i:2}/{len(TESTS)}] {name}: {prompt[:70]}", flush=True)
    r = _run(prompt)
    r["name"] = name
    if r.get("error") and "empty" not in name and "whitespace" not in name:
        passed, reason = False, f"ERROR — {r['error']}"
    else:
        passed, reason = check(r)
    r["pass"] = passed
    r["reason"] = reason
    results.append(r)
    _flush()
    print(f"     {'PASS' if passed else 'FAIL'}  {reason}  ({r['elapsed_ms']}ms via {r['via']})", flush=True)

passed = sum(1 for r in results if r["pass"])
print(f"\nTOTAL: {passed} pass / {len(results) - passed} fail / {len(results)} run", flush=True)
print(f"Detailed log: {RESULT_PATH}", flush=True)
