"""
Hosted lead-capture forms.

Each form is a user-built collection of fields rendered at a public URL
(`/f/<slug>`). Submissions are funneled through the existing
`/api/public/leads` endpoint using the form's bound intake key, then logged
as `nexus_lead_form_submissions` rows for attribution.

Endpoints:
  GET    /api/lead-forms              — list (auth)
  POST   /api/lead-forms               — create (auth, owner/admin)
  GET    /api/lead-forms/{id}          — fetch one (auth)
  PATCH  /api/lead-forms/{id}          — update (auth, owner/admin)
  DELETE /api/lead-forms/{id}          — archive (auth, owner/admin)

  GET    /api/public/forms/{slug}      — UNAUTH, returns form schema for
                                          the public form page to render.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_context
from config.db import get_conn

router = APIRouter(tags=["lead_forms"])

FORMS_TABLE = "nexus_lead_forms"
SUBS_TABLE = "nexus_lead_form_submissions"

# Whitelist of field keys the builder can include in a form. Keeping this
# fixed (rather than free-form) means the public POST handler can map each
# submission key onto the existing CRM contact fields without surprises.
ALLOWED_FIELD_KEYS = {
    "name", "email", "phone", "company", "title", "message", "budget",
    "timeline", "city", "industry",
}


# ── Helpers ─────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or uuid.uuid4().hex[:10]


def _validate_fields(fields: list) -> list:
    """Trim to a clean, deterministic list of {key, label, required}."""
    if not isinstance(fields, list):
        raise HTTPException(400, "fields must be a list")
    out = []
    seen = set()
    for f in fields:
        if not isinstance(f, dict):
            continue
        key = (f.get("key") or "").strip().lower()
        if key not in ALLOWED_FIELD_KEYS or key in seen:
            continue
        seen.add(key)
        out.append({
            "key": key,
            "label": (f.get("label") or key.title())[:60],
            "required": bool(f.get("required")),
        })
    if not out:
        # Always at least one field — default to email so the form
        # captures something useful.
        out.append({"key": "email", "label": "Email", "required": True})
    return out


def _ensure_unique_slug(conn, business_id: str, base: str, exclude_id: Optional[str] = None) -> str:
    slug = base
    n = 1
    while True:
        q = f"SELECT id FROM {FORMS_TABLE} WHERE business_id = ? AND slug = ?"
        params = [business_id, slug]
        if exclude_id:
            q += " AND id != ?"
            params.append(exclude_id)
        row = conn.execute(q, params).fetchone()
        if not row:
            return slug
        n += 1
        slug = f"{base}-{n}"


def _create_intake_key_for_form(business_id: str, user_id: str, label: str) -> str:
    """Mint a new intake key bound to this form. Returns the key id."""
    from api.routers.intake import _generate_raw_key, _hash_key, INTAKE_TABLE
    raw = _generate_raw_key()
    key_id = uuid.uuid4().hex
    prefix = raw[:12] + "…"
    conn = get_conn()
    try:
        conn.execute(
            f"""INSERT INTO {INTAKE_TABLE}
                (id, business_id, key_hash, key_prefix, label, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (key_id, business_id, _hash_key(raw), prefix, label[:80], _now(), user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return key_id


def _intake_key_raw_hash(key_id: str) -> Optional[str]:
    """Used only when sending test submissions — returns key hash for
    cross-reference. The raw key isn't stored, so server-side test triggers
    use the form_id path instead of the key path."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT key_hash FROM nexus_intake_keys WHERE id = ?", (key_id,)
        ).fetchone()
    finally:
        conn.close()
    return row["key_hash"] if row else None


def _row_to_dict(row) -> dict:
    d = dict(row)
    try:
        d["fields"] = json.loads(d.pop("fields_json") or "[]")
    except Exception:
        d["fields"] = []
    return d


# ── Models ──────────────────────────────────────────────────────────────────
class FormFieldIn(BaseModel):
    key: str
    label: Optional[str] = None
    required: bool = False


class FormCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field("", max_length=500)
    fields: List[FormFieldIn] = Field(default_factory=list)
    thank_you: Optional[str] = Field("", max_length=500)
    accent_color: Optional[str] = Field("#8b5cf6", max_length=16)
    slug: Optional[str] = Field(None, max_length=60)


class FormUpdateIn(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    fields: Optional[List[FormFieldIn]] = None
    thank_you: Optional[str] = Field(None, max_length=500)
    accent_color: Optional[str] = Field(None, max_length=16)


# ── Auth-gated routes ───────────────────────────────────────────────────────
@router.get("/api/lead-forms")
def list_forms(ctx: dict = Depends(get_current_context)):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""SELECT * FROM {FORMS_TABLE}
                 WHERE business_id = ? AND archived_at IS NULL
                 ORDER BY created_at DESC""",
            (ctx["business_id"],),
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


@router.post("/api/lead-forms")
def create_form(payload: FormCreateIn, ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can create lead forms")

    fields = _validate_fields([f.model_dump() for f in payload.fields])
    base_slug = _slugify(payload.slug or payload.title)

    conn = get_conn()
    try:
        slug = _ensure_unique_slug(conn, ctx["business_id"], base_slug)
    finally:
        conn.close()

    # Mint a key for this form.
    key_id = _create_intake_key_for_form(
        ctx["business_id"], ctx["user"]["id"],
        label=f"form:{slug}",
    )

    form_id = uuid.uuid4().hex
    now = _now()
    conn = get_conn()
    try:
        conn.execute(
            f"""INSERT INTO {FORMS_TABLE}
                (id, business_id, slug, intake_key_id, title, description,
                 fields_json, thank_you, accent_color, submit_count,
                 created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (
                form_id, ctx["business_id"], slug, key_id,
                payload.title.strip(), (payload.description or "").strip(),
                json.dumps(fields),
                (payload.thank_you or "Thanks — we'll be in touch.").strip(),
                (payload.accent_color or "#8b5cf6")[:16],
                now, ctx["user"]["id"],
            ),
        )
        conn.commit()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            f"SELECT * FROM {FORMS_TABLE} WHERE id = ?", (form_id,)
        ).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row)


@router.get("/api/lead-forms/{form_id}")
def get_form(form_id: str, ctx: dict = Depends(get_current_context)):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {FORMS_TABLE} WHERE id = ? AND business_id = ?",
            (form_id, ctx["business_id"]),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Form not found")
    return _row_to_dict(row)


@router.patch("/api/lead-forms/{form_id}")
def update_form(form_id: str, payload: FormUpdateIn,
                ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can edit lead forms")

    updates = {}
    if payload.title is not None:       updates["title"] = payload.title.strip()
    if payload.description is not None: updates["description"] = payload.description.strip()
    if payload.thank_you is not None:   updates["thank_you"] = payload.thank_you.strip()
    if payload.accent_color is not None: updates["accent_color"] = payload.accent_color[:16]
    if payload.fields is not None:
        updates["fields_json"] = json.dumps(_validate_fields(
            [f.model_dump() for f in payload.fields]
        ))
    if not updates:
        raise HTTPException(400, "No editable fields supplied")

    sets = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [form_id, ctx["business_id"]]
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            f"UPDATE {FORMS_TABLE} SET {sets} WHERE id = ? AND business_id = ?",
            params,
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Form not found")
        conn.commit()
        row = conn.execute(
            f"SELECT * FROM {FORMS_TABLE} WHERE id = ?", (form_id,)
        ).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row)


@router.delete("/api/lead-forms/{form_id}")
def archive_form(form_id: str, ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can archive lead forms")

    conn = get_conn()
    try:
        cur = conn.execute(
            f"UPDATE {FORMS_TABLE} SET archived_at = ? "
            f"WHERE id = ? AND business_id = ?",
            (_now(), form_id, ctx["business_id"]),
        )
        affected = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    if not affected:
        raise HTTPException(404, "Form not found")
    return {"ok": True}


# ── Public (unauthenticated) form schema ────────────────────────────────────
@router.get("/api/public/forms/{slug}")
def public_form_schema(slug: str):
    """Render-time fetch for the /f/<slug> page. Returns only what the
    public form needs — no business_id, no key, no internal IDs."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"""SELECT title, description, fields_json, thank_you,
                       accent_color, slug
                  FROM {FORMS_TABLE}
                 WHERE slug = ? AND archived_at IS NULL""",
            (slug,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Form not found")
    d = _row_to_dict(row)
    return d


# ── Internal helper used by /api/public/leads ───────────────────────────────
def lookup_form_by_slug(slug: str) -> Optional[dict]:
    """Used by the public-leads endpoint to look up form + key by slug."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"""SELECT f.id, f.business_id, f.intake_key_id, f.slug, f.title,
                       k.key_hash
                  FROM {FORMS_TABLE} f
                  JOIN nexus_intake_keys k ON k.id = f.intake_key_id
                 WHERE f.slug = ? AND f.archived_at IS NULL""",
            (slug,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def record_submission(business_id: str, form_id: str, contact_id: str,
                      channel: str = "") -> None:
    """Log a submission + bump the form's submit_count. Best-effort."""
    try:
        conn = get_conn()
        try:
            conn.execute(
                f"""INSERT INTO {SUBS_TABLE}
                    (id, business_id, form_id, contact_id, channel, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (uuid.uuid4().hex, business_id, form_id, contact_id,
                 (channel or "")[:40], _now()),
            )
            conn.execute(
                f"UPDATE {FORMS_TABLE} SET submit_count = submit_count + 1 "
                f"WHERE id = ?", (form_id,),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"[lead_forms] submission log failed: {e}")
