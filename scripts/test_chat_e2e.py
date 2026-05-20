"""End-to-end test pass against the chat agent using REAL workspace data.

Runs a battery of prompts through agent_loop.run_agent in-process (no
uvicorn needed). For each prompt, records:
  - fact-router catch (if any)
  - tools called (and their args)
  - final answer text
  - grounding warnings
  - pass/fail verdict against an expected behaviour

Output is a markdown table so we can see at a glance what's broken.
Cheap money-wise because most prompts hit fact_router (no LLM) and the
LLM calls are short.

Usage:
    python scripts/test_chat_e2e.py
"""
from __future__ import annotations

import os
import sys
import json
import time
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

# Look up the test user + business from Postgres so the script can be
# re-run as the underlying IDs change between resets.
def _resolve_user() -> Dict[str, str]:
    import psycopg
    url = None
    with open(os.path.join(REPO_ROOT, ".env"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not url:
        raise SystemExit("DATABASE_URL not found in .env")
    conn = psycopg.connect(url)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, name, role FROM nexus_users "
                    "WHERE email LIKE 'praneethhh%' ORDER BY created_at DESC LIMIT 1")
        u = cur.fetchone()
        if not u:
            raise SystemExit("No test user 'praneethhh*' found in nexus_users")
        # Pick the business with the most contacts — that's the one the
        # user has actually been testing in. A fresh "B2 The B" with zero
        # rows would make fact_router tests trivially empty.
        cur.execute("""
            SELECT b.id, b.name, COUNT(c.id) AS n
            FROM nexus_businesses b
            LEFT JOIN nexus_contacts c ON c.business_id = b.id
            WHERE b.owner_id = %s
            GROUP BY b.id, b.name
            ORDER BY n DESC, b.created_at DESC
            LIMIT 1
        """, (u[0],))
        b = cur.fetchone()
        if not b:
            raise SystemExit(f"User {u[1]} owns no business")
        return {
            "user_id": u[0], "user_email": u[1], "user_name": u[2], "user_role": u[3] or "owner",
            "business_id": b[0], "business_name": b[1],
        }
    finally:
        conn.close()


CTX = _resolve_user()
print(f"Test user:    {CTX['user_name']} ({CTX['user_email']})")
print(f"Business:     {CTX['business_name']} ({CTX['business_id']})")
print()


# ── Test runner ────────────────────────────────────────────────────────────
import concurrent.futures

PER_TEST_TIMEOUT = 60  # seconds — a single LLM call shouldn't take longer

def _run_one_inner(prompt: str) -> Dict[str, Any]:
    """The actual work; run inside a thread so the outer can enforce
    a wall-clock timeout when an LLM call hangs."""
    t0 = time.time()
    out: Dict[str, Any] = {"prompt": prompt, "via": None, "tools": [],
                           "answer": "", "warnings": [], "elapsed_ms": 0, "error": None}
    try:
        from agents import fact_router
        direct = fact_router.try_answer(prompt, CTX["business_id"])
        if direct:
            out["via"] = "fact_router"
            out["answer"] = direct
            out["elapsed_ms"] = int((time.time() - t0) * 1000)
            return out

        from agents.agent_loop import run_agent
        result = run_agent(
            messages=[{"role": "user", "content": prompt}],
            business_id=CTX["business_id"],
            business_name=CTX["business_name"],
            user_id=CTX["user_id"],
            user_name=CTX["user_name"],
            user_role=CTX["user_role"],
        )
        out["via"] = "agent_loop"
        out["answer"] = (result.get("answer") or "")[:400]
        out["tools"] = [tc.get("name") for tc in result.get("tool_calls", [])]
        out["warnings"] = result.get("grounding_warnings", [])
        out["stop_reason"] = result.get("stop_reason")
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out


def _run_one(prompt: str) -> Dict[str, Any]:
    """Wall-clock timeout wrapper. If the inner thread hasn't returned
    in PER_TEST_TIMEOUT seconds, abandon it and mark TIMEOUT — keeps a
    hung LLM call from blocking the whole test pass."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run_one_inner, prompt)
        try:
            return future.result(timeout=PER_TEST_TIMEOUT)
        except concurrent.futures.TimeoutError:
            return {"prompt": prompt, "via": "TIMEOUT", "tools": [],
                    "answer": "", "warnings": [],
                    "elapsed_ms": PER_TEST_TIMEOUT * 1000,
                    "error": f"hung for >{PER_TEST_TIMEOUT}s — abandoned"}


# ── Expectations ──────────────────────────────────────────────────────────
# Each test is (prompt, expect_via, expect_check). expect_check is a
# callable that returns (passed, reason) given the result dict.

def expect_count_answer(min_n: int = 1) -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        ans = r["answer"].lower()
        if "you have" in ans and ("contacts" in ans or "deals" in ans or "tasks" in ans
                                   or "invoices" in ans or "companies" in ans):
            return True, "OK"
        return False, f"answer doesn't look like a count: {ans[:80]!r}"
    return _chk


def expect_ordinal_answer(_chk_substr: Optional[str] = None) -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        ans = r["answer"].lower()
        if "contact" in ans or "deal" in ans or "invoice" in ans or "task" in ans:
            if _chk_substr and _chk_substr.lower() not in ans:
                return False, f"missing expected substring {_chk_substr!r} in {ans[:80]!r}"
            return True, "OK"
        return False, f"answer doesn't look like an ordinal: {ans[:80]!r}"
    return _chk


def expect_list_answer() -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        ans = r["answer"]
        # A list answer numbers its lines and contains at least 3 entries.
        if "1." in ans and "2." in ans and "3." in ans:
            return True, "OK"
        return False, f"no numbered list in answer: {ans[:120]!r}"
    return _chk


def expect_via(via: str) -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        if r["via"] != via:
            return False, f"routed via {r['via']}, expected {via}"
        return True, "OK"
    return _chk


def expect_no_grounding_warnings() -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        if r["warnings"]:
            return False, f"grounding flagged: {r['warnings']}"
        return True, "OK"
    return _chk


def expect_tool_called(name: str) -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        if name in r["tools"]:
            return True, "OK"
        return False, f"tool {name!r} not called. tools were: {r['tools']}"
    return _chk


def all_of(*checks) -> Callable[[Dict[str, Any]], tuple[bool, str]]:
    def _chk(r):
        for c in checks:
            ok, reason = c(r)
            if not ok:
                return False, reason
        return True, "OK"
    return _chk


# ── The test plan ─────────────────────────────────────────────────────────
TESTS: List[tuple[str, Callable]] = [
    # ── fact_router patterns (no LLM, must be deterministic) ──────────────
    ("how many contacts do I have?",
     all_of(expect_via("fact_router"), expect_count_answer())),
    ("how many deals?",
     all_of(expect_via("fact_router"), expect_count_answer())),
    ("how many tasks?",
     all_of(expect_via("fact_router"), expect_count_answer())),
    ("how many invoices?",
     all_of(expect_via("fact_router"), expect_count_answer())),

    ("list all contacts",
     all_of(expect_via("fact_router"), expect_list_answer())),
    ("show me my tasks",
     all_of(expect_via("fact_router"), expect_list_answer())),
    ("first 5 contacts",
     all_of(expect_via("fact_router"), expect_list_answer())),

    ("the 5th contact",
     all_of(expect_via("fact_router"), expect_ordinal_answer())),
    ("last invoice",
     all_of(expect_via("fact_router"), expect_ordinal_answer())),
    ("first deal",
     all_of(expect_via("fact_router"), expect_ordinal_answer())),

    ("phone numbers of all my contacts",
     all_of(expect_via("fact_router"), expect_list_answer())),
    ("emails of all contacts",
     all_of(expect_via("fact_router"), expect_list_answer())),

    # ── General-knowledge (should NOT trigger grounding refusal) ──────────
    ("how do I find new clients?",
     all_of(expect_via("agent_loop"), expect_no_grounding_warnings())),
    ("what are software industry trends?",
     all_of(expect_via("agent_loop"), expect_no_grounding_warnings())),

    # ── Contact lookups (LLM + find_contacts) ─────────────────────────────
    ("what is Praneeth P K's email?",
     all_of(expect_via("agent_loop"), expect_tool_called("find_contacts"))),
    ("find Praneeth PK",
     all_of(expect_via("agent_loop"), expect_tool_called("find_contacts"))),
    ("do I have a contact named Rahul?",
     all_of(expect_via("agent_loop"), expect_tool_called("find_contacts"))),

    # ── Email drafting (must call find_contacts THEN send_email) ──────────
    ("draft a mail to Praneeth P K about a business enquiry visit tomorrow at my place",
     all_of(expect_via("agent_loop"),
            expect_tool_called("find_contacts"),
            expect_tool_called("send_email"))),

    # ── Task creation (LLM + create_task) ────────────────────────────────
    ("create a task to follow up with Rahul tomorrow",
     all_of(expect_via("agent_loop"), expect_tool_called("create_task"))),
]


# ── Execute ───────────────────────────────────────────────────────────────
# Write results incrementally to a known file so we can see progress live
# (Python stdout in PowerShell + bash pipes is unreliably buffered, and a
# long-running LLM test that hangs leaves us with zero visibility into
# which case it died on). The file is overwritten on every run.
RESULT_PATH = os.path.join(REPO_ROOT, "scripts", "_test_chat_results.log")
results: List[Dict[str, Any]] = []

def _write_results() -> None:
    with open(RESULT_PATH, "w", encoding="utf-8") as fh:
        fh.write(f"User:     {CTX['user_name']} ({CTX['user_email']})\n")
        fh.write(f"Business: {CTX['business_name']} ({CTX['business_id']})\n\n")
        for i, r in enumerate(results, 1):
            tag = "PASS" if r["pass"] else "FAIL"
            fh.write(f"[{i:2}] {tag}  {r['prompt']}\n")
            fh.write(f"     via:     {r['via']}\n")
            fh.write(f"     elapsed: {r['elapsed_ms']}ms\n")
            fh.write(f"     reason:  {r['reason']}\n")
            if r.get("tools"):
                fh.write(f"     tools:   {r['tools']}\n")
            if r.get("warnings"):
                fh.write(f"     warns:   {r['warnings']}\n")
            if r.get("error"):
                fh.write(f"     ERROR:   {r['error']}\n")
            fh.write(f"     answer:  {r['answer'][:240]}\n\n")
        passed = sum(1 for r in results if r["pass"])
        fh.write(f"\nTOTAL: {passed} pass / {len(results) - passed} fail / {len(results)} run\n")

for i, (prompt, check) in enumerate(TESTS, 1):
    print(f"[{i:2}/{len(TESTS)}] {prompt[:80]}", flush=True)
    r = _run_one(prompt)
    if r.get("error"):
        passed, reason = False, f"ERROR — {r['error']}"
    else:
        passed, reason = check(r)
    r["pass"] = passed
    r["reason"] = reason
    results.append(r)
    _write_results()  # Flush after every test so a crash doesn't lose data.
    icon = "PASS" if passed else "FAIL"
    print(f"     {icon} {reason}  ({r['elapsed_ms']}ms via {r['via']})", flush=True)

passed = sum(1 for r in results if r["pass"])
print(f"\nTOTAL: {passed} pass / {len(results) - passed} fail / {len(results)} run", flush=True)
print(f"Detailed log: {RESULT_PATH}", flush=True)
