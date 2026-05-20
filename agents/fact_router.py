"""
Deterministic fact router — answers trivial factual queries with SQL,
bypassing the LLM entirely.

Why: LLMs hallucinate on "what is the 5th contact" because they have
to read row N of a list. SQL does this in O(1) with zero risk of
inventing 'John Doe'. The LLM should be reserved for fuzzy NL tasks
('draft an email to Rahul') where its strengths actually matter.

Public surface:
    try_answer(question, business_id) -> str | None
        - Returns a plain-text answer if the question matches a known
          deterministic pattern.
        - Returns None if the question needs the LLM (fall through).

Patterns covered (per entity: contacts, companies, deals, tasks,
invoices, leads):
    - "how many <entity>"     → SELECT COUNT(*)
    - "Nth / first / last <entity>"  → ORDER BY ... LIMIT 1 OFFSET (N-1)
    - "list / show <entity>"  (small N) → ORDER BY ... LIMIT N

Anything else (free-form questions, multi-entity reasoning, NL
verbs like 'draft', 'send', 'remember') falls through.

Safety:
    - Reads only. Never mutates.
    - Scoped by business_id - the same isolation the LLM tools use.
    - Bounded result size (max 25 rows for list queries) so we never
      dump a huge table into the chat.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Callable, List, Optional, Tuple

from config.db import get_conn


# ── Ordinal vocabulary ──────────────────────────────────────────────────────
_ORDINAL_WORDS = {
    "first": 1, "1st": 1, "one": 1,
    "second": 2, "2nd": 2, "two": 2,
    "third": 3, "3rd": 3, "three": 3,
    "fourth": 4, "4th": 4, "four": 4,
    "fifth": 5, "5th": 5, "five": 5,
    "sixth": 6, "6th": 6, "six": 6,
    "seventh": 7, "7th": 7, "seven": 7,
    "eighth": 8, "8th": 8, "eight": 8,
    "ninth": 9, "9th": 9, "nine": 9,
    "tenth": 10, "10th": 10, "ten": 10,
    "last": -1,    # special — means MAX index
}


def _parse_ordinal(s: str) -> Optional[int]:
    """Return 1-based position from a single token, or None.
       'last' -> -1 (caller resolves via total)."""
    s = s.lower().strip()
    if s in _ORDINAL_WORDS:
        return _ORDINAL_WORDS[s]
    # Bare integer with optional st/nd/rd/th suffix.
    m = re.fullmatch(r"(\d{1,3})(st|nd|rd|th)?", s)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 500 else None
    return None


# ── Entity definitions ──────────────────────────────────────────────────────
# Each entity exposes:
#   keywords:        synonyms the user might type
#   count_sql:       SELECT COUNT(*) ... WHERE business_id = ?
#   row_sql(limit, offset): list query for ordinal / list answers
#   format_row(row): one-line human description used for ordinal replies

def _row_contact(r) -> str:
    name = " ".join(filter(None, [(r["first_name"] or "").strip(), (r["last_name"] or "").strip()])).strip() or "(no name)"
    bits = [name]
    if r["title"]:  bits.append(r["title"])
    if r["email"]:  bits.append(r["email"])
    return " — ".join(bits)


def _row_company(r) -> str:
    bits = [r["name"] or "(unnamed company)"]
    if r["industry"]: bits.append(r["industry"])
    return " — ".join(bits)


def _row_deal(r) -> str:
    bits = [r["title"] or "(untitled deal)"]
    if r["stage"]: bits.append(f"stage: {r['stage']}")
    if r["amount"] is not None:
        try:
            bits.append(f"₹{int(r['amount']):,}")
        except Exception:
            pass
    return " — ".join(bits)


def _row_task(r) -> str:
    bits = [r["title"] or "(untitled task)"]
    if r["status"]:   bits.append(r["status"])
    if r["due_date"]: bits.append(f"due {r['due_date']}")
    return " — ".join(bits)


def _row_invoice(r) -> str:
    bits = [r["number"] or f"invoice #{r['id'][:8]}"]
    if r["status"]: bits.append(r["status"])
    if r["total_amount"] is not None:
        try:
            bits.append(f"₹{int(r['total_amount']):,}")
        except Exception:
            pass
    return " — ".join(bits)


ENTITIES = {
    "contact": {
        "keywords": ["contact", "contacts", "lead", "leads", "customer", "customers", "person", "people"],
        "table": "nexus_contacts",
        "order_by": "last_name ASC, first_name ASC",
        "columns": "id, first_name, last_name, email, phone, title",
        "row_fmt": _row_contact,
        "singular": "contact",
        "plural": "contacts",
    },
    "company": {
        "keywords": ["company", "companies", "account", "accounts", "organisation", "organization"],
        "table": "nexus_companies",
        "order_by": "name ASC",
        "columns": "id, name, industry, website",
        "row_fmt": _row_company,
        "singular": "company",
        "plural": "companies",
    },
    "deal": {
        "keywords": ["deal", "deals", "opportunity", "opportunities", "pipeline"],
        "table": "nexus_deals",
        "order_by": "created_at DESC",
        "columns": "id, title, stage, amount, contact_id",
        "row_fmt": _row_deal,
        "singular": "deal",
        "plural": "deals",
    },
    "task": {
        "keywords": ["task", "tasks", "todo", "todos", "to-do", "to-dos"],
        "table": "nexus_tasks",
        "order_by": "COALESCE(due_date, created_at) ASC",
        "columns": "id, title, status, due_date",
        "row_fmt": _row_task,
        "singular": "task",
        "plural": "tasks",
    },
    "invoice": {
        "keywords": ["invoice", "invoices", "bill", "bills"],
        "table": "nexus_invoices",
        "order_by": "issued_at DESC",
        "columns": "id, number, status, total_amount",
        "row_fmt": _row_invoice,
        "singular": "invoice",
        "plural": "invoices",
    },
}


def _match_entity(question: str) -> Optional[str]:
    """Pick the entity whose keywords appear in the question. Longest match
    wins (so 'customers' beats 'customer')."""
    q = " " + question.lower() + " "
    best: Tuple[int, Optional[str]] = (0, None)
    for ekey, e in ENTITIES.items():
        for kw in e["keywords"]:
            if f" {kw} " in q or f" {kw}?" in q or f" {kw}." in q or q.endswith(f" {kw}"):
                if len(kw) > best[0]:
                    best = (len(kw), ekey)
    return best[1]


# ── Query helpers ──────────────────────────────────────────────────────────
def _count(business_id: str, table: str) -> int:
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def _rows(business_id: str, table: str, columns: str, order_by: str,
          limit: int, offset: int = 0) -> List[dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            f"SELECT {columns} FROM {table} WHERE business_id = ? "
            f"ORDER BY {order_by} LIMIT ? OFFSET ?",
            (business_id, limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Pattern detectors ──────────────────────────────────────────────────────
_COUNT_RE = re.compile(
    r"\b(how many|number of|count of|total\s+\w+|total)\b",
    re.IGNORECASE,
)

# Capture an ordinal token before the entity keyword.
_ORDINAL_RE = re.compile(
    r"\b(?:the\s+)?(\w+)\s+(contact|contacts|lead|leads|customer|customers|"
    r"company|companies|account|accounts|deal|deals|opportunity|opportunities|"
    r"task|tasks|invoice|invoices)\b",
    re.IGNORECASE,
)


def _try_count(question: str, business_id: str, entity_key: str) -> Optional[str]:
    if not _COUNT_RE.search(question):
        return None
    e = ENTITIES[entity_key]
    n = _count(business_id, e["table"])
    return f"You have {n} {e['singular'] if n == 1 else e['plural']} in your CRM."


def _try_ordinal(question: str, business_id: str, entity_key: str) -> Optional[str]:
    for m in _ORDINAL_RE.finditer(question):
        word = m.group(1)
        n = _parse_ordinal(word)
        if n is None:
            continue
        e = ENTITIES[entity_key]
        if n == -1:
            total = _count(business_id, e["table"])
            if total == 0:
                return f"You don't have any {e['plural']} yet."
            n = total
        rows = _rows(business_id, e["table"], e["columns"], e["order_by"],
                     limit=1, offset=max(0, n - 1))
        if not rows:
            total = _count(business_id, e["table"])
            return (f"You only have {total} {e['plural']} — there's no #{n} to show. "
                    f"Add more from the {e['plural'].title()} page.")
        ordinal_label = (
            "1st" if n == 1 else "2nd" if n == 2 else "3rd" if n == 3
            else f"{n}th"
        )
        return f"The {ordinal_label} {e['singular']} is **{e['row_fmt'](rows[0])}**."
    return None


# ── Public entry point ────────────────────────────────────────────────────
def try_answer(question: str, business_id: str) -> Optional[str]:
    """If the question matches a known factual pattern, run SQL and return
    a plain-text answer. Otherwise return None — caller should hand off
    to the LLM agent."""
    if not question or not question.strip():
        return None
    q = question.strip()
    # Guard against very long prompts — the patterns are for short
    # factual asks. Anything 200+ chars is conversational.
    if len(q) > 240:
        return None
    entity = _match_entity(q)
    if not entity:
        return None
    # Order matters: a question can match both 'how many' and an
    # ordinal pattern; "how many" wins because it's the simpler ask.
    for fn in (_try_count, _try_ordinal):
        try:
            answer = fn(q, business_id, entity)
            if answer:
                return answer
        except Exception:
            # If SQL or pattern blows up, fall through to LLM.
            return None
    return None
