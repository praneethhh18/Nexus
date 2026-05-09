"""Inbound voice-call sessions — state for an in-progress AI receptionist call.

Lifecycle:
    1. Twilio POSTs `/api/voice/twilio-inbound` when a call comes in.
       → start_session(call_sid, business_id, from_number, twilio_to)
    2. After every speech-to-text turn, Twilio POSTs `/api/voice/twilio-gather`.
       → append_turn(call_sid, "user", speech_text) / "assistant", reply
    3. On hangup, Twilio POSTs `/api/voice/twilio-status` with CallStatus=completed.
       → finish_session(call_sid) → triggers post-call summarisation, CRM
         contact create/update, and the WhatsApp digest send

Storage: `nexus_inbound_call_sessions`. Uses Postgres-compatible JSON (TEXT)
columns so it works on both backends without a schema split.
"""
from __future__ import annotations

import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from typing import Any, Dict, List, Optional

from loguru import logger

from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_inbound_call_sessions"


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            call_sid       TEXT PRIMARY KEY,
            business_id    TEXT NOT NULL,
            twilio_to      TEXT,
            from_number    TEXT,
            started_at     TEXT NOT NULL,
            last_activity  TEXT NOT NULL,
            transcript     TEXT NOT NULL DEFAULT '[]',
            summary_json   TEXT,
            status         TEXT NOT NULL DEFAULT 'in_progress',
            ended_at       TEXT
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_biz ON {TABLE}(business_id, started_at DESC)"
    )
    conn.commit()
    return conn


def start_session(*, call_sid: str, business_id: str,
                   from_number: str, twilio_to: str) -> None:
    cols = ("call_sid", "business_id", "twilio_to", "from_number",
            "started_at", "last_activity", "transcript", "status")
    vals = (call_sid, business_id, twilio_to or "", from_number or "",
            now_iso(), now_iso(), "[]", "in_progress")
    conn = _conn()
    try:
        # ON CONFLICT keeps the original session if Twilio retries the inbound webhook
        # (it occasionally does on transient network blips).
        conn.execute(
            f"INSERT INTO {TABLE} ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' * len(cols))}) "
            f"ON CONFLICT(call_sid) DO NOTHING",
            vals,
        )
        conn.commit()
    finally:
        conn.close()


def get_session(call_sid: str) -> Optional[Dict[str, Any]]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE call_sid = ?",
            (call_sid,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["transcript"] = json.loads(d["transcript"] or "[]")
    except Exception:
        d["transcript"] = []
    if d.get("summary_json"):
        try:
            d["summary"] = json.loads(d["summary_json"])
        except Exception:
            d["summary"] = {}
    return d


def append_turn(call_sid: str, role: str, text: str) -> List[Dict[str, str]]:
    """Append one turn to the transcript and return the updated transcript."""
    sess = get_session(call_sid)
    if not sess:
        logger.warning(f"[inbound_calls] append_turn for unknown call_sid={call_sid}")
        return []
    transcript = sess.get("transcript") or []
    transcript.append({"role": role, "text": (text or "").strip(), "t": now_iso()})
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET transcript = ?, last_activity = ? WHERE call_sid = ?",
            (json.dumps(transcript, ensure_ascii=False), now_iso(), call_sid),
        )
        conn.commit()
    finally:
        conn.close()
    return transcript


def finish_session(call_sid: str, summary: Optional[Dict[str, Any]] = None,
                    status: str = "completed") -> Optional[Dict[str, Any]]:
    """Mark the session done and stash the summary blob. Returns the final row."""
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET status = ?, ended_at = ?, summary_json = ? "
            f"WHERE call_sid = ?",
            (status, now_iso(),
             json.dumps(summary, ensure_ascii=False) if summary is not None else None,
             call_sid),
        )
        conn.commit()
    finally:
        conn.close()
    return get_session(call_sid)


def list_recent_inbound(business_id: str, limit: int = 25) -> List[Dict[str, Any]]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT call_sid, business_id, twilio_to, from_number, "
            f"started_at, ended_at, status FROM {TABLE} "
            f"WHERE business_id = ? ORDER BY started_at DESC LIMIT ?",
            (business_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
