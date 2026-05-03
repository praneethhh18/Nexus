"""
Voice-call records — full transcripts + lead-gen summaries from the lab.

Storage shape (table `nexus_voice_calls`):
    id                TEXT PRIMARY KEY            internal id (vc-…)
    business_id       TEXT NOT NULL
    contact_id        TEXT                        nullable for ad-hoc calls
    call_sid          TEXT UNIQUE                 Twilio's CallSid
    started_at        TEXT
    ended_at          TEXT
    duration_sec      INTEGER
    outcome           TEXT                        from summary.outcome enum
    headline          TEXT                        one-line for activity feed
    lead_score        INTEGER                     0-100
    interest_level    TEXT                        hot|warm|cold|none
    sentiment         TEXT                        positive|neutral|negative
    next_step         TEXT
    callback_requested_at TEXT                    ISO 8601 or null
    transcript_json   TEXT                        full turns array as JSON
    summary_json      TEXT                        full summary blob as JSON
    watch_url         TEXT                        link to lab's /calls/<sid>
    created_at        TEXT
    created_by        TEXT
"""
from __future__ import annotations

import json
import sqlite3  # sqlite3.Row sentinel
import uuid
from typing import Optional, List, Dict, Any

from loguru import logger

from config.db import get_conn
from utils.timez import now_iso

VOICE_CALLS_TABLE = "nexus_voice_calls"


def _conn():
    conn = get_conn()
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {VOICE_CALLS_TABLE} (
        id                       TEXT PRIMARY KEY,
        business_id              TEXT NOT NULL,
        contact_id               TEXT,
        call_sid                 TEXT UNIQUE,
        started_at               TEXT,
        ended_at                 TEXT,
        duration_sec             INTEGER,
        outcome                  TEXT,
        headline                 TEXT,
        lead_score               INTEGER,
        interest_level           TEXT,
        sentiment                TEXT,
        next_step                TEXT,
        callback_requested_at    TEXT,
        transcript_json          TEXT,
        summary_json             TEXT,
        watch_url                TEXT,
        created_at               TEXT NOT NULL,
        created_by               TEXT
    )""")
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_voice_calls_biz "
        f"ON {VOICE_CALLS_TABLE}(business_id, started_at DESC)"
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_voice_calls_contact "
        f"ON {VOICE_CALLS_TABLE}(contact_id, started_at DESC)"
    )
    conn.commit()
    return conn


def store_completed_call(payload: Dict[str, Any], *,
                         created_by: str = "vox") -> Dict:
    """
    Persist the lab's callback payload as one row, plus a `nexus_interactions`
    entry so the contact's call history shows in the existing CRM timeline.

    Returns the saved record.
    """
    business_id = payload.get("business_id") or ""
    contact_id  = payload.get("contact_id") or None
    call_sid    = payload.get("call_sid") or ""
    summary     = payload.get("summary") or {}
    turns       = payload.get("turns") or []

    vc_id = f"vc-{uuid.uuid4().hex[:12]}"
    row = {
        "id":                    vc_id,
        "business_id":           business_id,
        "contact_id":            contact_id,
        "call_sid":              call_sid,
        "started_at":            payload.get("started_at"),
        "ended_at":              payload.get("ended_at"),
        "duration_sec":          payload.get("duration_sec"),
        "outcome":               summary.get("outcome"),
        "headline":              summary.get("headline"),
        "lead_score":            summary.get("lead_score"),
        "interest_level":        summary.get("interest_level"),
        "sentiment":             summary.get("sentiment"),
        "next_step":             summary.get("next_step"),
        "callback_requested_at": summary.get("callback_requested_at"),
        "transcript_json":       json.dumps(turns, ensure_ascii=False),
        "summary_json":          json.dumps(summary, ensure_ascii=False),
        "watch_url":             payload.get("watch_url"),
        "created_at":            now_iso(),
        "created_by":            created_by,
    }

    cols = ", ".join(row.keys())
    placeholders = ", ".join("?" * len(row))
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {VOICE_CALLS_TABLE} ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(call_sid) DO UPDATE SET "
            + ", ".join(f"{c}=excluded.{c}" for c in row.keys() if c != "id"),
            tuple(row.values()),
        )
        conn.commit()
    finally:
        conn.close()

    # Mirror as a CRM interaction so the contact's existing timeline picks it up.
    if contact_id and business_id:
        try:
            from api.crm import INTERACTIONS_TABLE
            interaction_id = f"in-{uuid.uuid4().hex[:10]}"
            conn = get_conn()
            conn.execute(
                f"INSERT INTO {INTERACTIONS_TABLE} "
                f"(id, business_id, contact_id, type, subject, summary, "
                f"occurred_at, created_at, created_by) "
                f"VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    interaction_id, business_id, contact_id, "call",
                    f"Voice call · {summary.get('outcome','call')}",
                    summary.get("headline") or "Voice call summary unavailable",
                    payload.get("ended_at") or now_iso(),
                    now_iso(),
                    created_by,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"[voice_calls] interaction mirror failed: {e}")

    # Mirror the headline + outcome to the contact's denormalized fields so
    # the existing CRM views ('last call' columns) light up immediately.
    if contact_id and business_id:
        try:
            from api.crm import CONTACTS_TABLE
            conn = get_conn()
            conn.execute(
                f"UPDATE {CONTACTS_TABLE} SET "
                f"  last_called_at = ?, last_call_outcome = ?, "
                f"  last_call_summary = ?, updated_at = ? "
                f"WHERE id = ? AND business_id = ?",
                (
                    payload.get("ended_at") or now_iso(),
                    summary.get("outcome") or "",
                    (summary.get("headline") or "")[:500],
                    now_iso(),
                    contact_id,
                    business_id,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"[voice_calls] contact denorm update failed: {e}")

    logger.info(
        f"[voice_calls] stored {vc_id} · contact={contact_id} "
        f"outcome={row['outcome']} score={row['lead_score']}"
    )
    return row


def list_for_contact(business_id: str, contact_id: str,
                     limit: int = 25) -> List[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT id, call_sid, started_at, ended_at, duration_sec, "
            f"  outcome, headline, lead_score, interest_level, sentiment, "
            f"  next_step, callback_requested_at, watch_url "
            f"FROM {VOICE_CALLS_TABLE} "
            f"WHERE business_id = ? AND contact_id = ? "
            f"ORDER BY started_at DESC LIMIT ?",
            (business_id, contact_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def list_for_business(business_id: str, limit: int = 50) -> List[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT id, contact_id, call_sid, started_at, ended_at, "
            f"  duration_sec, outcome, headline, lead_score, interest_level, "
            f"  sentiment, next_step, callback_requested_at, watch_url "
            f"FROM {VOICE_CALLS_TABLE} "
            f"WHERE business_id = ? "
            f"ORDER BY started_at DESC LIMIT ?",
            (business_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_call(business_id: str, vc_id_or_sid: str) -> Optional[Dict]:
    """Fetch one call's full record (including transcript + summary) by id or call_sid."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {VOICE_CALLS_TABLE} "
            f"WHERE business_id = ? AND (id = ? OR call_sid = ?)",
            (business_id, vc_id_or_sid, vc_id_or_sid),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    # Inflate JSON columns for the caller's convenience.
    try:
        d["turns"] = json.loads(d.pop("transcript_json") or "[]")
    except json.JSONDecodeError:
        d["turns"] = []
    try:
        d["summary"] = json.loads(d.pop("summary_json") or "{}")
    except json.JSONDecodeError:
        d["summary"] = {}
    return d
