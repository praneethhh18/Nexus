"""
Client-error receiver — accepts reports from the frontend's errorReporter.

Writes into `nexus_client_errors`. An admin can list the last N via
`GET /api/errors/recent` from the Settings > Diagnostics panel (UI follow-up).

Intentionally unauthenticated on POST: the path runs during render failures
where the token wrapper may itself be broken. Rate-limited at the middleware
layer just like every other endpoint.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import get_current_context
from config.db import get_conn
from utils.timez import now_iso

router = APIRouter(prefix="/api/errors", tags=["errors"])

TABLE = "nexus_client_errors"
_MAX_FIELD_CHARS = 4000


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT NOT NULL,
            business_id TEXT,
            user_id     TEXT,
            name        TEXT,
            message     TEXT,
            url         TEXT,
            user_agent  TEXT,
            release     TEXT,
            stack       TEXT,
            context     TEXT
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_received "
        f"ON {TABLE}(received_at DESC)"
    )
    conn.commit()
    return conn


def _trim(v: Any) -> str:
    if v is None:
        return ""
    s = str(v)
    return s[:_MAX_FIELD_CHARS]


@router.post("")
def submit_error(body: dict):
    """Accept a client error report. Never raises — reporter must not cascade."""
    try:
        import json as _json
        conn = _conn()
        try:
            conn.execute(
                f"INSERT INTO {TABLE} (received_at, business_id, user_id, name, "
                f"message, url, user_agent, release, stack, context) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    now_iso(),
                    _trim(body.get("business_id")),
                    _trim(body.get("user_id")),
                    _trim(body.get("name")),
                    _trim(body.get("message")),
                    _trim(body.get("url")),
                    _trim(body.get("userAgent")),
                    _trim(body.get("release")),
                    _trim(body.get("stack")),
                    _trim(_json.dumps(body.get("context") or {})),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"[errors] submit failed: {e}")
    # Always 200 — the reporter should never retry or surface.
    return {"ok": True}


@router.get("/recent")
def recent(limit: int = 50, ctx: dict = Depends(get_current_context)) -> List[Dict]:
    """Admin view of recent client errors. Owner/admin only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can read error reports")
    limit = max(1, min(int(limit or 50), 500))
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT id, received_at, business_id, user_id, name, message, "
            f"url, user_agent, release FROM {TABLE} "
            f"ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
