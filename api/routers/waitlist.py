"""
Waitlist / early-access sign-ups from the landing page.

POST /api/waitlist  — save email + chosen tier, return 201.
GET  /api/waitlist  — admin-only: list all sign-ups.
"""
from __future__ import annotations

import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from loguru import logger

from config.db import get_conn
from api.auth import require_role

router = APIRouter(prefix="/api/waitlist", tags=["waitlist"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class WaitlistEntry(BaseModel):
    email: str
    tier: str = "Pro"
    name: str = ""

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        allowed = {"Free", "Starter", "Pro", "Business", "Self-hosted"}
        if v not in allowed:
            raise ValueError(f"tier must be one of {allowed}")
        return v


def _ensure_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            email     TEXT    NOT NULL,
            tier      TEXT    NOT NULL DEFAULT 'Pro',
            name      TEXT    NOT NULL DEFAULT '',
            signed_up TEXT    NOT NULL,
            UNIQUE(email)
        )
    """)
    conn.commit()


@router.post("", status_code=201)
def join_waitlist(entry: WaitlistEntry):
    with get_conn() as conn:
        _ensure_table(conn)
        try:
            conn.execute(
                "INSERT INTO waitlist (email, tier, name, signed_up) VALUES (?, ?, ?, ?)",
                (entry.email, entry.tier, entry.name, datetime.utcnow().isoformat()),
            )
            conn.commit()
            logger.info(f"[Waitlist] {entry.email} → {entry.tier}")
        except Exception:
            # UNIQUE constraint — already signed up
            raise HTTPException(status_code=409, detail="Already on the waitlist.")
    return {"ok": True, "message": "You're on the list — we'll be in touch."}


@router.get("")
def list_waitlist(admin=Depends(require_role("admin"))):
    with get_conn() as conn:
        _ensure_table(conn)
        rows = conn.execute(
            "SELECT id, email, tier, name, signed_up FROM waitlist ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]
