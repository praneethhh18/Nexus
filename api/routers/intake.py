"""
Public lead-capture intake.

Two distinct surfaces:

  POST /api/public/leads     — UNAUTHENTICATED. Takes a workspace intake key
                                (in the body or X-Intake-Key header), validates
                                + rate-limits, creates a contact in that
                                workspace tagged source='public_form'. Returns
                                a small ack — no internal IDs, no error
                                reflections, just `{ok: true|false}`.

  GET  /api/intake/keys      — Auth-gated (workspace member). List keys for
                                the caller's workspace.
  POST /api/intake/keys      — Auth-gated (admin/owner). Create a new key.
                                Returns the *raw* key once; we only store
                                its SHA-256.
  DELETE /api/intake/keys/{id} — Revoke a key (admin/owner).

Storage: `nexus_intake_keys` (created by db/migrations/0002).

Privacy + abuse posture:
  - Raw key is never stored. We hash with SHA-256 and store key_hash.
  - The displayed prefix (`nx_pub_a1b2…`) lets the user identify which
    key is which without revealing the full secret.
  - Public endpoint is rate-limited per IP (in-memory token bucket — fine
    for the MVP, swap for Redis when we have multiple workers).
  - On a key validation miss the response is a generic 401, no detail
    leaked about whether the key exists / is revoked / belongs elsewhere.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_context
from config.settings import DB_PATH

router = APIRouter(tags=["intake"])

INTAKE_TABLE = "nexus_intake_keys"
KEY_PREFIX = "nx_pub_"


# ── Helpers ─────────────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_raw_key() -> str:
    """Public form keys are intentionally long + URL-safe so they can be
    pasted into a script tag without escaping."""
    return f"{KEY_PREFIX}{secrets.token_urlsafe(28)}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Rate-limit state — in-process. Resets on restart, fine for MVP.
_RATE_BUCKETS: dict[str, list[float]] = {}
_RATE_WINDOW_SEC = 60
_RATE_MAX = 10        # 10 requests / minute per (ip, key) combo


def _rate_limit_check(ip: str, key_prefix: str) -> bool:
    """True if the request should proceed. Drops anything older than the
    window from the bucket; returns False if the bucket is full."""
    bucket_id = f"{ip}|{key_prefix}"
    now = time.time()
    window_start = now - _RATE_WINDOW_SEC
    bucket = [t for t in _RATE_BUCKETS.get(bucket_id, []) if t > window_start]
    if len(bucket) >= _RATE_MAX:
        _RATE_BUCKETS[bucket_id] = bucket
        return False
    bucket.append(now)
    _RATE_BUCKETS[bucket_id] = bucket
    return True


# ── Models ──────────────────────────────────────────────────────────────────
class PublicLeadIn(BaseModel):
    """Public form payload. Only declared fields are accepted; anything else
    is silently dropped to keep the surface small + predictable."""
    intake_key: Optional[str] = Field(None, description="Workspace key (or use X-Intake-Key header)")
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=40)
    company: Optional[str] = Field(None, max_length=200)
    message: Optional[str] = Field(None, max_length=2000)


class IntakeKeyCreate(BaseModel):
    label: Optional[str] = Field(None, max_length=80)


# ── Public POST /api/public/leads ───────────────────────────────────────────
@router.post("/api/public/leads")
def receive_public_lead(payload: PublicLeadIn, request: Request):
    """
    Accept a lead from a public web form. Auth via a workspace intake key.
    """
    raw_key = (
        payload.intake_key
        or request.headers.get("X-Intake-Key")
        or ""
    ).strip()
    if not raw_key:
        # Generic — don't leak which header we expected, since this is a
        # public endpoint and any introspection helps an attacker.
        raise HTTPException(401, "Unauthorized")

    # Rate limit BEFORE the DB lookup so a flood of bad keys doesn't hammer SQLite.
    ip = (request.client.host if request.client else "unknown")[:45]
    key_prefix_for_bucket = raw_key[:12]  # prefix is enough to bucket per-key
    if not _rate_limit_check(ip, key_prefix_for_bucket):
        raise HTTPException(429, "Too many requests")

    key_hash = _hash_key(raw_key)
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT id, business_id, revoked_at FROM {INTAKE_TABLE} WHERE key_hash = ?",
            (key_hash,),
        ).fetchone()
        if not row or row["revoked_at"]:
            raise HTTPException(401, "Unauthorized")

        business_id = row["business_id"]
        now = _now()

        # Update key usage stats — best-effort.
        try:
            conn.execute(
                f"UPDATE {INTAKE_TABLE} SET last_used_at = ?, use_count = use_count + 1 WHERE id = ?",
                (now, row["id"]),
            )
            conn.commit()
        except Exception as e:
            logger.debug(f"[Intake] usage stat update failed: {e}")
    finally:
        conn.close()

    # Now create / dedup the contact via the existing CRM module so we get
    # the right table init + indexing for free.
    from api import crm as _crm

    email = (payload.email or "").strip().lower()
    phone = (payload.phone or "").strip()
    name_parts = (payload.name or "").strip().split(None, 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Dedup: if the workspace already has a contact with this email or phone,
    # don't create a duplicate — log a CRM interaction on the existing one.
    existing_id = None
    if email or phone:
        existing = _crm.list_contacts(business_id, search=email or phone, limit=10)
        for c in existing:
            if email and (c.get("email") or "").lower() == email:
                existing_id = c["id"]; break
            if phone and (c.get("phone") or "") == phone:
                existing_id = c["id"]; break

    contact_id: str
    deduped = False
    if existing_id:
        contact_id = existing_id
        deduped = True
    else:
        contact = _crm.create_contact(business_id, "system:public-form", {
            "first_name": first_name,
            "last_name":  last_name,
            "email":      email,
            "phone":      phone,
        })
        contact_id = contact["id"]

        # Stamp the source. crm.create_contact doesn't accept `source` yet
        # (kept narrow on purpose) — we set it directly here.
        try:
            conn = _conn()
            conn.execute(
                "UPDATE nexus_contacts SET source = ? WHERE id = ?",
                ("public_form", contact_id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"[Intake] source stamp failed: {e}")

    # Log the form submission as an interaction for full timeline visibility.
    try:
        summary_parts = []
        if payload.company: summary_parts.append(f"Company: {payload.company}")
        if payload.message: summary_parts.append(f"\n{payload.message}")
        _crm.create_interaction(business_id, "system:public-form", {
            "type": "note",
            "subject": "Public lead form submission",
            "summary": "".join(summary_parts) or "(no message)",
            "contact_id": contact_id,
        })
    except Exception as e:
        logger.warning(f"[Intake] interaction log failed: {e}")

    # Notify the workspace that a lead arrived.
    try:
        from api import notifications as _notifs
        title = "New lead via public form"
        msg = f"{payload.name}" + (f" · {payload.company}" if payload.company else "")
        if deduped:
            msg += " — already in your CRM, logged as an interaction."
        _notifs.push(
            title=title, message=msg,
            severity="info", type="lead",
            business_id=business_id,
        )
    except Exception as e:
        logger.warning(f"[Intake] notification push failed: {e}")

    return {"ok": True, "deduped": deduped}


# ── Auth-gated key management ───────────────────────────────────────────────
@router.get("/api/intake/keys")
def list_keys(ctx: dict = Depends(get_current_context)):
    """List intake keys for the caller's workspace. Anyone in the workspace
    can see the prefixes; only the raw key is hidden."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""SELECT id, key_prefix, label, created_at, created_by,
                       revoked_at, last_used_at, use_count
                  FROM {INTAKE_TABLE}
                 WHERE business_id = ?
                 ORDER BY revoked_at NULLS FIRST, created_at DESC""",
            (ctx["business_id"],),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@router.post("/api/intake/keys")
def create_key(payload: IntakeKeyCreate, ctx: dict = Depends(get_current_context)):
    """Create a new intake key. The RAW key is returned exactly once —
    on subsequent reads only the prefix is visible."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can create intake keys")

    raw = _generate_raw_key()
    key_id = uuid.uuid4().hex
    prefix = raw[:12] + "…"
    now = _now()

    conn = _conn()
    try:
        conn.execute(
            f"""INSERT INTO {INTAKE_TABLE}
                (id, business_id, key_hash, key_prefix, label, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                key_id, ctx["business_id"], _hash_key(raw), prefix,
                (payload.label or "")[:80], now, ctx["user"]["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "id": key_id, "key": raw, "key_prefix": prefix,
        "label": payload.label or "", "created_at": now,
    }


@router.delete("/api/intake/keys/{key_id}")
def revoke_key(key_id: str, ctx: dict = Depends(get_current_context)):
    """Revoke a key. Doesn't delete the row (we keep it for audit history)."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can revoke intake keys")

    if not re.fullmatch(r"[a-f0-9]{32}", key_id):
        raise HTTPException(400, "Invalid key id")

    conn = _conn()
    try:
        cur = conn.execute(
            f"UPDATE {INTAKE_TABLE} SET revoked_at = ? WHERE id = ? AND business_id = ?",
            (_now(), key_id, ctx["business_id"]),
        )
        affected = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    if affected == 0:
        raise HTTPException(404, "Key not found")
    return {"ok": True}
