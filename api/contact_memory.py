"""Per-contact memory — small structured facts the agents accumulate over time.

Echo (the existing memory keeper) writes to a business-wide store. This file
keeps a separate, *contact-scoped* store so when the agent calls Mehta the
next time, Vox can preface the call with "you mentioned cost concerns last
time and your CFO Anjali needs to approve." That's the difference between
"AI assistant" and "AI teammate who remembers your customers."

What goes here:
    - Communicated preferences:   "prefers Net-30", "no email — WhatsApp only"
    - Stated objections:          "pricing pushback on tier 2"
    - Internal context:           "CFO Anjali approves > ₹3L"
    - Promises made/received:     "promised quote by Friday"
    - Personal touches:           "kids' school admissions in May"

What doesn't:
    - Generic call/email transcripts (those live in nexus_voice_calls /
      nexus_interactions). Memory is the *distilled* takeaway.

Storage: `nexus_contact_memory`, scoped by business + contact. Multiple rows
per contact (each row = one fact). Soft-delete via `archived_at` rather
than DELETE so we can audit what was forgotten and when.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_contact_memory"

VALID_KINDS = ("preference", "objection", "context", "promise", "personal", "note")


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id            TEXT PRIMARY KEY,
            business_id   TEXT NOT NULL,
            contact_id    TEXT NOT NULL,
            kind          TEXT NOT NULL DEFAULT 'note',
            fact          TEXT NOT NULL,
            source        TEXT,            -- 'call', 'email', 'whatsapp', 'manual', 'agent'
            source_ref    TEXT,            -- e.g. call_sid or interaction id
            confidence    INTEGER DEFAULT 80,
            created_at    TEXT NOT NULL,
            created_by    TEXT,
            archived_at   TEXT
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_lookup "
        f"ON {TABLE}(business_id, contact_id, archived_at)"
    )
    conn.commit()
    return conn


def _validate_kind(kind: str) -> str:
    k = (kind or "note").lower().strip()
    if k not in VALID_KINDS:
        return "note"
    return k


def remember(*, business_id: str, contact_id: str, fact: str,
              kind: str = "note", source: str = "manual",
              source_ref: Optional[str] = None,
              confidence: int = 80,
              created_by: Optional[str] = None) -> Dict[str, Any]:
    """Store one fact about a contact. Idempotent within a business+contact —
    if the same fact is added twice, the second call updates the timestamp
    instead of creating a duplicate row."""
    fact = (fact or "").strip()
    if not fact:
        raise ValueError("fact is required")
    if len(fact) > 1000:
        raise ValueError("fact too long (max 1000 chars)")

    # De-dup: same business + contact + fact text → bump created_at, keep id
    existing = _find_duplicate(business_id, contact_id, fact)
    if existing:
        conn = _conn()
        try:
            conn.execute(
                f"UPDATE {TABLE} SET created_at = ?, archived_at = NULL, "
                f"source = ?, source_ref = ? WHERE id = ?",
                (now_iso(), source, source_ref, existing["id"]),
            )
            conn.commit()
        finally:
            conn.close()
        return get_one(business_id, existing["id"])

    mid = f"cm-{uuid.uuid4().hex[:10]}"
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {TABLE} (id, business_id, contact_id, kind, fact, "
            f"source, source_ref, confidence, created_at, created_by) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?)",
            (mid, business_id, contact_id, _validate_kind(kind), fact,
             source, source_ref, max(0, min(100, int(confidence))),
             now_iso(), created_by),
        )
        conn.commit()
    finally:
        conn.close()
    return get_one(business_id, mid)


def _find_duplicate(business_id: str, contact_id: str, fact: str) -> Optional[Dict[str, Any]]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? AND contact_id = ? "
            f"AND fact = ? LIMIT 1",
            (business_id, contact_id, fact),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def get_one(business_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE id = ? AND business_id = ?",
            (memory_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def recall(business_id: str, contact_id: str,
            include_archived: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
    """Return all known facts about a contact, freshest first."""
    sql = (f"SELECT id, kind, fact, source, source_ref, confidence, "
           f"created_at, archived_at FROM {TABLE} "
           f"WHERE business_id = ? AND contact_id = ?")
    params: list = [business_id, contact_id]
    if not include_archived:
        sql += " AND archived_at IS NULL"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def forget(business_id: str, memory_id: str) -> bool:
    """Soft-delete a memory. Returns True if a row was archived."""
    conn = _conn()
    try:
        cur = conn.execute(
            f"UPDATE {TABLE} SET archived_at = ? "
            f"WHERE id = ? AND business_id = ? AND archived_at IS NULL",
            (now_iso(), memory_id, business_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def build_brief(business_id: str, contact_id: str, max_facts: int = 8) -> str:
    """Render a compact human-friendly brief for prompt injection.

    Used by Vox / Iris / Outreach to preface their drafts with what the
    agent already knows about this contact, so the recipient feels heard
    rather than spoken-at.
    """
    facts = recall(business_id, contact_id, limit=max_facts)
    if not facts:
        return ""

    by_kind: Dict[str, List[str]] = {}
    for f in facts:
        by_kind.setdefault(f["kind"], []).append(f["fact"])

    parts: List[str] = ["What we know about this contact:"]
    order = ("preference", "objection", "context", "promise", "personal", "note")
    for k in order:
        items = by_kind.get(k)
        if not items:
            continue
        label = k.title()
        for it in items[:3]:
            parts.append(f"  • [{label}] {it}")
    return "\n".join(parts)


def auto_extract_from_call(*, business_id: str, contact_id: str,
                            call_sid: str, transcript: List[Dict[str, str]],
                            summary: Dict[str, Any]) -> int:
    """Run after a call ends — distil the transcript into 1-3 memory facts.

    Cheap LLM call. Best-effort — if extraction fails, the call summary is
    still stored, this just doesn't add per-contact memories.
    """
    if not contact_id or not transcript:
        return 0
    try:
        from config import llm_provider

        convo = "\n".join(
            f"{('Customer' if t.get('role') == 'user' else 'Us')}: {t.get('text','').strip()}"
            for t in transcript[-30:] if t.get("text")
        )
        system = (
            "Extract 1 to 3 SHORT durable facts about THIS contact from the "
            "call transcript. Each fact must be useful next time we talk to "
            "them — preferences, objections, internal context, promises, "
            "personal touches. Skip generic stuff. Output one fact per line, "
            "no numbering, no quotes. Each line under 120 characters. If "
            "nothing useful, output nothing."
        )
        prompt = (
            f"Call summary: {summary.get('headline','')}\n"
            f"Outcome: {summary.get('outcome','')}\n\n"
            f"Transcript:\n{convo[:3000]}"
        )
        raw = llm_provider.invoke(prompt, system=system, max_tokens=300, temperature=0.2)
    except Exception as e:
        logger.warning(f"[contact_memory] auto-extract LLM failed for call {call_sid}: {e}")
        return 0

    saved = 0
    for line in (raw or "").splitlines():
        fact = line.strip(" •-*\t").strip()
        if not fact or len(fact) < 8:
            continue
        try:
            remember(
                business_id=business_id, contact_id=contact_id,
                fact=fact[:500], kind="note", source="call", source_ref=call_sid,
                confidence=70, created_by="agent",
            )
            saved += 1
        except Exception as e:
            logger.debug(f"[contact_memory] save failed for fact {fact[:60]!r}: {e}")
    if saved:
        logger.info(f"[contact_memory] saved {saved} fact(s) for contact={contact_id} from call={call_sid}")
    return saved
