"""
Business memory — long-term facts and preferences the agent should remember.

Each business has its own memory bank. The agent auto-injects recent/relevant
entries into its context, and can itself call tools to remember/recall/forget.

Examples of good memory entries:
    - "We bill NET-30 by default; invoices remind at 7/14/21 days past due."
    - "Preferred Slack channel for alerts: #sales-ops"
    - "Our pricing tier A is $5,000/mo; tier B is $12,000/mo."

This is NOT the same as conversation history — it's persistent, structured,
per-business knowledge the AI can rely on across sessions.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH

MEMORY_TABLE = "nexus_business_memory"


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {MEMORY_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        kind TEXT DEFAULT 'fact',
        content TEXT NOT NULL,
        tags TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        created_by TEXT,
        is_pinned INTEGER DEFAULT 0
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_mem_biz ON {MEMORY_TABLE}(business_id, is_pinned, updated_at)")
    conn.commit()
    return conn


def _now() -> str:
    return datetime.utcnow().isoformat()


def _validate_content(content: str) -> str:
    content = (content or "").strip()
    if not content:
        raise HTTPException(400, "Memory content cannot be empty")
    if len(content) > 2000:
        raise HTTPException(400, "Memory content too long (max 2000)")
    return content


# ── CRUD ────────────────────────────────────────────────────────────────────
def add_memory(business_id: str, user_id: str, content: str, kind: str = "fact",
               tags: str = "", is_pinned: bool = False) -> Dict[str, Any]:
    content = _validate_content(content)
    mid = f"mem-{uuid.uuid4().hex[:10]}"
    now = _now()
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {MEMORY_TABLE} "
            f"(id, business_id, kind, content, tags, created_at, updated_at, created_by, is_pinned) "
            f"VALUES (?,?,?,?,?,?,?,?,?)",
            (mid, business_id, kind[:40], content, tags[:300], now, now, user_id, int(bool(is_pinned))),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info(f"[Memory] Added {mid} biz={business_id}")
    return get_memory(business_id, mid)


def get_memory(business_id: str, memory_id: str) -> Dict[str, Any]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {MEMORY_TABLE} WHERE id = ? AND business_id = ?",
            (memory_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Memory not found")
    return dict(row)


def list_memory(business_id: str, search: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        if search:
            rows = conn.execute(
                f"SELECT * FROM {MEMORY_TABLE} WHERE business_id = ? "
                f"AND (content LIKE ? OR tags LIKE ?) "
                f"ORDER BY is_pinned DESC, updated_at DESC LIMIT ?",
                (business_id, f"%{search}%", f"%{search}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {MEMORY_TABLE} WHERE business_id = ? "
                f"ORDER BY is_pinned DESC, updated_at DESC LIMIT ?",
                (business_id, limit),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def update_memory(business_id: str, memory_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    get_memory(business_id, memory_id)  # existence check
    allowed = {"content", "kind", "tags", "is_pinned"}
    fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not fields:
        raise HTTPException(400, "No editable fields provided")
    if "content" in fields:
        fields["content"] = _validate_content(fields["content"])
    if "is_pinned" in fields:
        fields["is_pinned"] = int(bool(fields["is_pinned"]))

    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [_now(), memory_id, business_id]
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {MEMORY_TABLE} SET {sets}, updated_at = ? WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return get_memory(business_id, memory_id)


def delete_memory(business_id: str, memory_id: str) -> None:
    get_memory(business_id, memory_id)
    conn = _get_conn()
    try:
        conn.execute(
            f"DELETE FROM {MEMORY_TABLE} WHERE id = ? AND business_id = ?",
            (memory_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Context injection for the agent ─────────────────────────────────────────
def build_memory_context(business_id: str, query: str = "", max_entries: int = 12) -> str:
    """
    Return a text block of the most relevant memory entries for this business,
    to inject into the agent's system prompt. Pinned entries always come first,
    then a keyword-filtered slice if a query is provided.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        pinned = conn.execute(
            f"SELECT kind, content FROM {MEMORY_TABLE} "
            f"WHERE business_id = ? AND is_pinned = 1 ORDER BY updated_at DESC",
            (business_id,),
        ).fetchall()

        others = []
        if query and len(query) > 2:
            # crude keyword match — good enough for a few hundred entries
            tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 2][:5]
            if tokens:
                like_clauses = " OR ".join(["LOWER(content) LIKE ?" for _ in tokens])
                params = [business_id] + [f"%{t}%" for t in tokens] + [max_entries]
                others = conn.execute(
                    f"SELECT kind, content FROM {MEMORY_TABLE} "
                    f"WHERE business_id = ? AND is_pinned = 0 "
                    f"AND ({like_clauses}) ORDER BY updated_at DESC LIMIT ?",
                    params,
                ).fetchall()

        if not others:
            others = conn.execute(
                f"SELECT kind, content FROM {MEMORY_TABLE} "
                f"WHERE business_id = ? AND is_pinned = 0 "
                f"ORDER BY updated_at DESC LIMIT ?",
                (business_id, max_entries),
            ).fetchall()
    finally:
        conn.close()

    lines = []
    for r in pinned:
        lines.append(f"[pinned/{r['kind']}] {r['content']}")
    for r in others[:max_entries]:
        lines.append(f"[{r['kind']}] {r['content']}")
    if not lines:
        return ""
    return "Known facts about this business:\n" + "\n".join(f"- {l}" for l in lines)
