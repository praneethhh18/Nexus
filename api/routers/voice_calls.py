"""
Voice-calls router — connects NexusAgent's CRM to the calling-room lab.

Endpoints:
    POST /api/voice/dial                    auth-gated; operator triggers a call
    POST /api/voice/callback                public + signed; lab posts results here
    GET  /api/voice/calls                   recent calls for the current business
    GET  /api/voice/calls/{id_or_sid}       one call (transcript + summary)
    GET  /api/voice/contacts/{contact_id}/calls   call history for a contact

The lab (nexuscaller-lab/voice_agent/server.py) lives at LAB_URL (env var,
e.g. http://localhost:8765). Twilio audio bridges, transcript storage, and
summary generation all happen there. NexusAgent only orchestrates and
persists results.
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3  # sqlite3.Row sentinel
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Request

from loguru import logger

from api import voice_calls
from api.auth import get_current_context
from api.crm import CONTACTS_TABLE
from config.db import get_conn
from utils.timez import now_iso


router = APIRouter(tags=["voice_calls"])


def _lab_url() -> str:
    """Internal server-to-server URL (e.g. http://vox-server:8765 in Docker)."""
    url = (os.getenv("LAB_URL") or os.getenv("VOX_LAB_URL") or "").rstrip("/")
    if not url:
        raise HTTPException(
            500,
            "LAB_URL not configured — set it in NexusAgent/.env to the "
            "voice-agent server URL (e.g. http://vox-server:8765 in Docker, "
            "http://localhost:8765 in local dev).",
        )
    return url


def _vox_public_url() -> str:
    """Browser-reachable URL for the vox server's precall / cockpit pages.
    In Docker this differs from LAB_URL (the internal network address).
    Set VOX_PUBLIC_URL=https://vox.yourdomain.com in production .env.
    Falls back to LAB_URL for local dev where both point to localhost:8765.
    """
    return (os.getenv("VOX_PUBLIC_URL") or _lab_url()).rstrip("/")


def _public_callback_url() -> str:
    """The lab POSTs back here when a call ends. Must be reachable from the lab.
    Set NEXUS_PUBLIC_URL=https://app.yourdomain.com in production .env.
    """
    base = (os.getenv("NEXUS_PUBLIC_URL")
            or f"http://localhost:{os.getenv('NEXUS_PORT', '8000')}")
    return base.rstrip("/") + "/api/voice/callback"


# ── Build the call payload from a contact_id (shared by dial + prepare) ─
def _build_payload_for_contact(business_id: str, contact_id: str,
                                body: dict) -> dict:
    """Assemble the payload the lab's /api/dial expects, given a CRM contact."""
    contact = None
    if contact_id:
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                f"SELECT * FROM {CONTACTS_TABLE} "
                f"WHERE id = ? AND business_id = ?",
                (contact_id, business_id),
            ).fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(404, f"contact {contact_id} not found")
        contact = dict(row)

    phone = ((contact or {}).get("phone") or body.get("phone") or "").strip()
    if not phone:
        raise HTTPException(400, "no phone number on the contact and none in the body")
    if not phone.startswith("+"):
        raise HTTPException(400, f"phone must be E.164 (start with +): {phone!r}")

    contact_name = (
        body.get("contact_name")
        or " ".join(filter(None, [
            (contact or {}).get("first_name"),
            (contact or {}).get("last_name"),
        ])).strip()
        or "there"
    )

    # Pull the business profile for the agent's pitch context.
    business_name = "Nexus"
    business_blurb = "We help businesses run smarter operations."
    try:
        from api.businesses import get_business
        biz = get_business(business_id) or {}
        business_name = biz.get("name") or business_name
        for k in ("description", "about", "blurb", "notes"):
            if biz.get(k):
                business_blurb = biz[k].strip()
                break
    except Exception as e:
        logger.debug(f"[voice/dial] could not fetch business {business_id}: {e}")

    return {
        "phone":           phone,
        "contact_id":      contact_id or "",
        "business_id":     business_id,
        "contact_name":    contact_name,
        "business_name":   business_name,
        "business_blurb":  business_blurb,
        "agent_name":      os.getenv("VOX_AGENT_NAME", "Vox"),
        "purpose":         (body.get("purpose") or "a quick check-in").strip(),
        "callback_url":    _public_callback_url(),
    }


# ── Operator-triggered dial (legacy direct-dial — used by the inline modal) ─
@router.post("/api/voice/dial")
async def dial_contact(
    body: dict,
    ctx: dict = Depends(get_current_context),
):
    """Direct dial — places the call immediately with the default Groq+ElevenLabs
    stack. Kept for the inline-modal flow and any programmatic callers.
    UI now prefers /api/voice/prepare-dial → opens the lab's precall page first."""
    business_id = ctx["business_id"]
    user_id = ctx["user"]["id"]
    contact_id = (body.get("contact_id") or "").strip()

    payload = _build_payload_for_contact(business_id, contact_id, body)
    lab_url = _lab_url()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(f"{lab_url}/api/dial", json=payload)
    except Exception as e:
        logger.exception(f"[voice/dial] lab unreachable at {lab_url}: {e}")
        raise HTTPException(502, f"lab unreachable: {e}")

    if r.status_code != 200:
        raise HTTPException(502, f"lab returned HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data.get("ok"):
        raise HTTPException(400, data.get("error", "lab refused the dial"))

    watch_path = data.get("watch_url") or f"/calls/{data.get('call_sid','')}"
    watch_url = f"{lab_url}{watch_path}"
    logger.info(
        f"[voice/dial] biz={business_id} user={user_id} "
        f"contact={contact_id or 'adhoc'} → call_sid={data.get('call_sid')}"
    )
    return {"ok": True, "call_sid": data["call_sid"], "watch_url": watch_url}


# ── Prepare-dial — returns a precall URL the operator opens in a new tab ──
@router.post("/api/voice/prepare-dial")
async def prepare_dial(
    body: dict,
    ctx: dict = Depends(get_current_context),
):
    """Build the call payload, encode it, and return the lab's /precall URL.

    The operator's browser opens the URL in a new tab. The precall page
    lets them pick a stack combo (or customize), then dials. Audio runs in
    the lab; results come back through /api/voice/callback (existing flow).
    """
    business_id = ctx["business_id"]
    contact_id = (body.get("contact_id") or "").strip()

    payload = _build_payload_for_contact(business_id, contact_id, body)

    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")

    lab_url = _vox_public_url()  # must be browser-reachable, not the internal Docker URL
    precall_url = f"{lab_url}/precall?p={encoded}"

    logger.info(
        f"[voice/prepare-dial] biz={business_id} contact={contact_id} "
        f"phone={payload['phone']} → precall_url generated"
    )
    return {"ok": True, "precall_url": precall_url}


# ── Lab callback ─────────────────────────────────────────────────────────
@router.post("/api/voice/callback")
async def voice_callback(
    request: Request,
    x_voice_callback_secret: Optional[str] = Header(None, alias="X-Voice-Callback-Secret"),
):
    """The lab POSTs the full call record here after the call ends.
    Stored in nexus_voice_calls + mirrored as a CRM interaction."""
    expected = os.getenv("VOICE_CALLBACK_SECRET", "")
    if expected and x_voice_callback_secret != expected:
        logger.warning("[voice/callback] rejected: bad / missing secret")
        raise HTTPException(401, "bad callback secret")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "body must be JSON")

    if not payload.get("call_sid"):
        raise HTTPException(400, "call_sid is required")

    # business_id may be empty for ad-hoc CLI calls — store anyway, just won't
    # mirror to CRM. Real CRM-triggered calls always have it.
    record = voice_calls.store_completed_call(payload, created_by="vox")
    return {"ok": True, "id": record["id"]}


# ── Read APIs (for the CRM frontend) ─────────────────────────────────────
@router.get("/api/voice/calls")
def list_recent_calls(
    limit: int = 50,
    ctx: dict = Depends(get_current_context),
):
    return {"calls": voice_calls.list_for_business(ctx["business_id"], limit=limit)}


@router.get("/api/voice/calls/{vc_id_or_sid}")
def get_one_call(
    vc_id_or_sid: str,
    ctx: dict = Depends(get_current_context),
):
    rec = voice_calls.get_call(ctx["business_id"], vc_id_or_sid)
    if not rec:
        raise HTTPException(404, f"no voice call with id={vc_id_or_sid}")
    return rec


@router.get("/api/voice/contacts/{contact_id}/calls")
def list_contact_calls(
    contact_id: str,
    limit: int = 25,
    ctx: dict = Depends(get_current_context),
):
    return {
        "contact_id": contact_id,
        "calls": voice_calls.list_for_contact(ctx["business_id"], contact_id, limit=limit),
    }
