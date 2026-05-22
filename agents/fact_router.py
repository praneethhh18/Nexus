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
    # Real schema: nexus_deals has `name` + `value` (NOT title/amount).
    bits = [r["name"] or "(unnamed deal)"]
    if r["stage"]: bits.append(f"stage: {r['stage']}")
    if r["value"] is not None:
        try:
            bits.append(f"₹{int(r['value']):,}")
        except Exception:
            pass
    return " — ".join(bits)


def _row_task(r) -> str:
    bits = [r["title"] or "(untitled task)"]
    if r["status"]:   bits.append(r["status"])
    if r["due_date"]: bits.append(f"due {r['due_date']}")
    return " — ".join(bits)


def _row_invoice(r) -> str:
    # Real schema: nexus_invoices has `total` (NOT total_amount) and
    # `issue_date` (NOT issued_at).
    bits = [r["number"] or f"invoice #{r['id'][:8]}"]
    if r["status"]: bits.append(r["status"])
    if r["total"] is not None:
        try:
            bits.append(f"₹{int(r['total']):,}")
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
        # nexus_deals real columns: name (not title), value (not amount).
        "columns": "id, name, stage, value, contact_id",
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
        # nexus_invoices real columns: issue_date (not issued_at), total
        # (not total_amount).
        "order_by": "issue_date DESC",
        "columns": "id, number, status, total",
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
          limit: int, offset: int = 0,
          extra_where: str = "", extra_params: tuple = ()) -> List[dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            f"SELECT {columns} FROM {table} "
            f"WHERE business_id = ? {extra_where} "
            f"ORDER BY {order_by} LIMIT ? OFFSET ?",
            (business_id, *extra_params, limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Status filter detection ──────────────────────────────────────────────────
# When the user says "pending tasks" / "open invoices" / "paid invoices",
# pin the list query to that status. Without this, _try_list would return
# every task regardless of status, which makes the answer look broken.
_TASK_STATUS_FILTERS = {
    "pending":     ("open", "pending"),
    "open":        ("open", "pending"),
    "in progress": ("in_progress",),
    "in-progress": ("in_progress",),
    "ongoing":     ("in_progress",),
    "active":      ("open", "pending", "in_progress"),
    "incomplete":  ("open", "pending", "in_progress"),
    "todo":        ("open", "pending"),
    "to do":       ("open", "pending"),
    "to-do":       ("open", "pending"),
    "done":        ("done", "completed"),
    "completed":   ("done", "completed"),
    "finished":    ("done", "completed"),
    "closed":      ("done", "completed"),
}
_INVOICE_STATUS_FILTERS = {
    "open":     ("open", "sent"),
    "pending":  ("open", "sent"),
    "unpaid":   ("open", "sent", "overdue"),
    "overdue":  ("overdue",),
    "paid":     ("paid",),
    "draft":    ("draft",),
    "sent":     ("sent",),
}


def _status_filter_for(entity_key: str, question: str) -> Optional[Tuple[str, tuple]]:
    """Inspect the question for a status word relevant to this entity.
    Returns (where_fragment, params) suitable for splicing into _rows().
    Longest-match wins so 'in progress' beats 'in'."""
    q = " " + question.lower() + " "
    table = {"task": _TASK_STATUS_FILTERS, "invoice": _INVOICE_STATUS_FILTERS}.get(entity_key)
    if not table:
        return None
    best: Tuple[int, Optional[Tuple[str, ...]]] = (0, None)
    for word, statuses in table.items():
        # Match the status word as a whole token in the question.
        if f" {word} " in q or f" {word}?" in q or f" {word}." in q or q.endswith(f" {word}"):
            if len(word) > best[0]:
                best = (len(word), statuses)
    if not best[1]:
        return None
    placeholders = ", ".join(["?"] * len(best[1]))
    return (f"AND LOWER(status) IN ({placeholders})", tuple(best[1]))


# ── Pattern detectors ──────────────────────────────────────────────────────
# Count detection. The previous regex matched 'number of' anywhere in
# the sentence, which caught 'contact number of all of them' as a
# count query. We now require the count phrase to appear in a counting
# context — not when the user is asking about phone numbers / emails.
_COUNT_RE = re.compile(
    r"\b(how many|count of|total\s+\w+|total number of)\b|"
    r"\bnumber of\b(?!\s+(?:them|us|you|those|these|all|the\s+contacts?))",
    re.IGNORECASE,
)

# Field-extract — 'phone numbers of all contacts', 'emails of my leads'.
# Catches the user asking for one field across the list.
_FIELD_RE = re.compile(
    r"\b(phone\s*number|phone|mobile|email|email\s*address|address|title|role|job\s*title|company)s?\b",
    re.IGNORECASE,
)
_FIELD_MAP = {
    "phone": "phone", "phone number": "phone", "mobile": "phone",
    "email": "email", "email address": "email",
    "title": "title", "role": "title", "job title": "title",
}
# When the user asks 'contact numbers', that's a phone-number request,
# NOT a count. We need to detect this BEFORE the count router runs.
_PHONE_INTENT_RE = re.compile(
    r"\b(contact\s+number|phone\s+number|mobile\s+number|whatsapp\s+number)s?\b",
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
    status_filter = _status_filter_for(entity_key, question)
    if status_filter:
        extra_where, extra_params = status_filter
        conn = get_conn()
        try:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM {e['table']} "
                f"WHERE business_id = ? {extra_where}",
                (business_id, *extra_params),
            ).fetchone()
            n = int(row[0]) if row else 0
        finally:
            conn.close()
        return f"You have {n} matching {e['singular'] if n == 1 else e['plural']}."
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


# "list/show/give me all my contacts" — any verb that asks for the data set.
_LIST_RE = re.compile(
    r"\b(list|show|give\s+me|display|see|view|all\s+(of\s+)?my|all\s+the|all\s+(?=\w+))\b",
    re.IGNORECASE,
)
# "first 10 deals" / "top 5 contacts" — a bounded slice from the front.
_TOP_N_RE = re.compile(
    r"\b(first|top|next)\s+(\d{1,2})\b",
    re.IGNORECASE,
)


def _try_fields(question: str, business_id: str, entity_key: str) -> Optional[str]:
    """Handle 'phone numbers of all contacts', 'emails of leads',
    'contact numbers' etc. Returns a tidy 'Name — value' list.

    Only fires for `contact` entity right now (the only one with phone
    + email columns in scope). Other entities fall through."""
    if entity_key != "contact":
        return None
    # Detect the explicit phone-intent phrases first.
    phone_intent = bool(_PHONE_INTENT_RE.search(question))
    field_match = _FIELD_RE.search(question)
    if not phone_intent and not field_match:
        return None

    # Decide which column to pull.
    if phone_intent:
        col = "phone"
    else:
        token = field_match.group(1).lower().replace("  ", " ").strip()
        col = _FIELD_MAP.get(token)
        if col is None:
            return None

    # Decide whether this is a single-contact field question (let the
    # LLM handle, since it can match by name) or a list-all-fields
    # question (we handle deterministically). Three signals point at
    # the list interpretation:
    #   1. A list verb (list / show / give me / ...).
    #   2. A possessive ('of all', 'of them', 'of my', 'of the').
    #   3. The bare phone-intent phrase by itself ('contact numbers',
    #      'phone numbers', 'mobile numbers') — unambiguously plural
    #      and the user obviously wants everyone, not one specific
    #      person they haven't named.
    is_list_intent = (
        _LIST_RE.search(question)
        or re.search(r"\bof\s+(them|all|my|the)\b", question, re.IGNORECASE)
        or (phone_intent and len(question.split()) <= 4)
    )
    if not is_list_intent:
        return None

    e = ENTITIES[entity_key]
    rows = _rows(business_id, e["table"], e["columns"], e["order_by"],
                 limit=50, offset=0)
    if not rows:
        return f"You don't have any {e['plural']} yet."

    label = {"phone": "Phone", "email": "Email", "title": "Title"}.get(col, col.title())
    lines = []
    for i, r in enumerate(rows):
        name = " ".join(filter(None, [(r["first_name"] or "").strip(),
                                       (r["last_name"] or "").strip()])).strip() or "(no name)"
        val = (r.get(col) or "").strip() if isinstance(r, dict) else (r[col] or "").strip()
        lines.append(f"{i + 1}. {name} — {val or '(no ' + col + ' on file)'}")
    return f"{label}s for your {len(rows)} {e['plural']}:\n\n" + "\n".join(lines)


def _try_list(question: str, business_id: str, entity_key: str) -> Optional[str]:
    """Catch the broad 'show me my <entity>' style asks. This is the
    pattern that previously hit the LLM and produced fabricated lists.

    Returns up to 25 rows formatted one per line. For totals > 25 we
    append a 'showing N of total' footer so the user knows there's
    more, with a pointer to the dedicated page.

    Triggers on EITHER:
      - a list verb (list/show/give me/display/all-of-my/...), or
      - an explicit slice ('first 5 contacts', 'top 10 deals',
        'next 3 invoices') — without this, 'first 5 contacts' was
        getting hijacked by _try_ordinal which captured '5' as the
        ordinal and returned a single 5th-contact answer.

    Honors a status filter when present ('pending tasks', 'paid
    invoices', etc.) — without this we'd return ALL tasks for
    'show me my pending tasks' which makes the bot look broken."""
    if not _LIST_RE.search(question) and not _TOP_N_RE.search(question):
        return None
    e = ENTITIES[entity_key]
    status_filter = _status_filter_for(entity_key, question)
    extra_where, extra_params = (status_filter or ("", ()))

    # Total count — respect the status filter so the header says
    # "5 pending tasks" not "5 of 14".
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM {e['table']} "
            f"WHERE business_id = ? {extra_where}",
            (business_id, *extra_params),
        ).fetchone()
        total = int(row[0]) if row else 0
    finally:
        conn.close()

    if total == 0:
        if status_filter:
            return f"You don't have any matching {e['plural']} right now."
        return (f"You don't have any {e['plural']} yet. "
                f"Add your first {e['singular']} from the {e['plural'].title()} page.")

    # Honor 'first N' / 'top N' if present, otherwise default to 25.
    requested = 25
    m = _TOP_N_RE.search(question)
    if m:
        requested = min(max(int(m.group(2)), 1), 50)

    rows = _rows(business_id, e["table"], e["columns"], e["order_by"],
                 limit=requested, offset=0,
                 extra_where=extra_where, extra_params=extra_params)
    lines = [f"{i + 1}. {e['row_fmt'](r)}" for i, r in enumerate(rows)]
    qualifier = ""
    if status_filter:
        # Pull the user's chosen word verbatim back into the header so
        # they see we honored their filter ("Here are your pending tasks…").
        q_low = " " + question.lower() + " "
        for word in sorted(
            list((_TASK_STATUS_FILTERS if entity_key == "task" else _INVOICE_STATUS_FILTERS).keys()),
            key=len, reverse=True,
        ):
            if f" {word} " in q_low or f" {word}?" in q_low or f" {word}." in q_low or q_low.endswith(f" {word}"):
                qualifier = f"{word} "
                break
    header = (
        f"Here are all {total} of your {qualifier}{e['plural']}:"
        if len(rows) >= total
        else f"Showing the first {len(rows)} of {total} {qualifier}{e['plural']} "
             f"(open the {e['plural'].title()} page for the full list):"
    )
    return header + "\n\n" + "\n".join(lines)


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
    # Order matters:
    #   fields (phones / emails) FIRST — 'contact numbers' would otherwise
    #     trip the count regex and answer with the wrong question.
    #   count next   — 'how many contacts' is the simplest answer.
    #   list BEFORE ordinal — 'first 5 contacts' is a list-of-five, NOT
    #     the 5th contact. _try_list now triggers on _TOP_N_RE too, so
    #     it claims this case before _try_ordinal can mis-match the '5'.
    #   ordinal LAST — '5th contact' / 'last deal' / a bare 'first
    #     contact' (no number) still hit this because none of the
    #     earlier handlers match those.
    for fn in (_try_fields, _try_count, _try_list, _try_ordinal):
        try:
            answer = fn(q, business_id, entity)
            if answer:
                return answer
        except Exception as e:
            # If SQL or pattern blows up, log loudly so we don't ship
            # broken router patterns silently — previously a schema
            # mismatch (e.g. column 'amount' on nexus_deals where the
            # real column is 'value') would just fall through to the
            # LLM with no visible signal that the deterministic path
            # was broken.
            import logging
            logging.getLogger(__name__).exception(
                f"[fact_router] {fn.__name__} crashed on q={q!r} "
                f"entity={entity!r}: {e}"
            )
            return None
    return None
