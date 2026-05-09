"""Voice-call (Vox) tools for the agent.

Lets the agent place outbound calls in response to user requests like:
    "call +91 98765 43210 and ask about the status of order INV-2087"

When the request originates over WhatsApp, the result summary is mirrored
back to the user via WhatsApp once the call ends. The CRM call log + contact
denormalization happens automatically through the existing voice_callback
handler — no extra work needed there.

Wiring:
    WhatsApp inbound (api/whatsapp.py)
      → sets WHATSAPP_ORIGIN.set(phone)
      → run_agent → invokes dial_contact tool
        → POSTs to LAB_URL/api/dial
        → records pending row mapping call_sid → whatsapp_phone
    Lab finishes call → POSTs to /api/voice/callback
      → store_completed_call (CRM mirror, contact denorm)
      → send WhatsApp summary if pending row exists
"""
from __future__ import annotations

import contextvars
import os
import re
import sqlite3  # sqlite3.Row sentinel
from typing import Optional, Dict, Any

import httpx
from loguru import logger

from agents.tool_registry import register_tool
from config.db import get_conn
from utils.timez import now_iso

# Set by whatever channel triggered the agent run, so the tool knows where
# to deliver the summary when the call completes asynchronously.
WHATSAPP_ORIGIN: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "whatsapp_origin", default=None,
)

PENDING_TABLE = "nexus_voice_pending_whatsapp"


# ── Pending-callback table (one row per in-flight call from WhatsApp) ───────
def _ensure_pending_table() -> None:
    conn = get_conn()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {PENDING_TABLE} (
                call_sid       TEXT PRIMARY KEY,
                business_id    TEXT NOT NULL,
                user_id        TEXT NOT NULL,
                whatsapp_phone TEXT NOT NULL,
                purpose        TEXT,
                target_phone   TEXT,
                target_name    TEXT,
                created_at     TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def record_pending_call(*, call_sid: str, business_id: str, user_id: str,
                        whatsapp_phone: str, purpose: str,
                        target_phone: str, target_name: str) -> None:
    _ensure_pending_table()
    cols = ("call_sid", "business_id", "user_id", "whatsapp_phone",
            "purpose", "target_phone", "target_name", "created_at")
    vals = (call_sid, business_id, user_id, whatsapp_phone, purpose,
            target_phone, target_name, now_iso())
    conn = get_conn()
    try:
        # Postgres-compatible upsert that also works on SQLite (both support
        # ON CONFLICT). The unique target is the PRIMARY KEY (call_sid).
        conn.execute(
            f"INSERT INTO {PENDING_TABLE} ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' * len(cols))}) "
            f"ON CONFLICT(call_sid) DO UPDATE SET "
            + ", ".join(f"{c}=excluded.{c}" for c in cols if c != "call_sid"),
            vals,
        )
        conn.commit()
    finally:
        conn.close()


def get_pending_call(call_sid: str) -> Optional[Dict[str, Any]]:
    _ensure_pending_table()
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {PENDING_TABLE} WHERE call_sid = ?",
            (call_sid,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def clear_pending_call(call_sid: str) -> None:
    _ensure_pending_table()
    conn = get_conn()
    try:
        conn.execute(f"DELETE FROM {PENDING_TABLE} WHERE call_sid = ?", (call_sid,))
        conn.commit()
    finally:
        conn.close()


# ── Phone helpers ───────────────────────────────────────────────────────────
def _normalize_phone(phone: str, default_cc: str = "+91") -> str:
    """Coerce common SMS/WhatsApp phone formats into E.164.

    Accepts: +919876543210, 919876543210, 9876543210, 98765 43210
    Rejects: empty / less than 8 digits.
    Default country code is +91 (India) — matches the SMB target market.
    """
    s = re.sub(r"[^\d+]", "", phone or "")
    if not s:
        raise ValueError("phone is empty")
    if s.startswith("+"):
        if len(s) < 9:  # +CCN — 8 digits min after the +
            raise ValueError(f"phone too short: {phone!r}")
        return s
    if len(s) == 10:           # bare 10-digit Indian mobile
        return default_cc + s
    if len(s) == 12 and s.startswith("91"):
        return "+" + s
    if len(s) >= 8:
        return "+" + s
    raise ValueError(f"phone too short or unrecognised: {phone!r}")


def _find_or_create_contact(business_id: str, user_id: str,
                             phone: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Look up a CRM contact by phone; create a minimal one if none exists."""
    from api import crm as _crm

    # Try search by phone (handles slight format differences)
    digits = re.sub(r"\D", "", phone)
    last10 = digits[-10:] if len(digits) >= 10 else digits
    for c in _crm.list_contacts(business_id, search=last10, limit=10):
        c_digits = re.sub(r"\D", "", (c.get("phone") or ""))
        if c_digits.endswith(last10):
            return c

    nm = (name or "").strip() or "WhatsApp lead"
    parts = nm.split(" ", 1)
    payload = {
        "first_name": parts[0],
        "last_name":  parts[1] if len(parts) > 1 else None,
        "phone":      phone,
        "source":     "whatsapp",
    }
    return _crm.create_contact(business_id, user_id, payload)


# ── The tool itself ─────────────────────────────────────────────────────────
def _dial_contact(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    user_id     = ctx["user_id"]
    raw_phone   = (args.get("phone") or "").strip()
    if not raw_phone:
        raise ValueError("phone is required")
    phone = _normalize_phone(raw_phone)

    purpose      = (args.get("purpose") or "a quick check-in").strip()[:300]
    contact_name = (args.get("contact_name") or "").strip()
    contact_id   = (args.get("contact_id") or "").strip()

    # Look up or create the CRM contact (so the call gets attached to a record)
    if not contact_id:
        try:
            c = _find_or_create_contact(business_id, user_id, phone, name=contact_name)
            contact_id = c.get("id") or ""
            if not contact_name:
                contact_name = " ".join(filter(None, [
                    c.get("first_name"), c.get("last_name"),
                ])).strip() or "there"
        except Exception as e:
            logger.warning(f"[voice_tools] contact lookup/create failed for {phone}: {e}")
            # Still allow the call — pass an empty contact_id; lab handles ad-hoc.

    # Build the lab payload
    lab_url = (os.getenv("LAB_URL") or os.getenv("VOX_LAB_URL") or "").rstrip("/")
    if not lab_url:
        raise RuntimeError(
            "LAB_URL is not configured — set it in .env to the Vox lab server "
            "(e.g. http://localhost:8765)"
        )

    callback_base = (os.getenv("NEXUS_PUBLIC_URL")
                     or f"http://localhost:{os.getenv('NEXUS_PORT', '8000')}").rstrip("/")
    callback_url = callback_base + "/api/voice/callback"

    business_name  = "Nexus"
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
        logger.debug(f"[voice_tools] business profile lookup failed: {e}")

    payload = {
        "phone":          phone,
        "contact_id":     contact_id,
        "business_id":    business_id,
        "contact_name":   contact_name or "there",
        "business_name":  business_name,
        "business_blurb": business_blurb,
        "agent_name":     os.getenv("VOX_AGENT_NAME", "Vox"),
        "purpose":        purpose,
        "callback_url":   callback_url,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(f"{lab_url}/api/dial", json=payload)
    except Exception as e:
        raise RuntimeError(f"Vox lab unreachable at {lab_url}: {e}")

    if r.status_code != 200:
        raise RuntimeError(f"Vox lab returned HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "Vox lab refused the dial"))

    call_sid  = data.get("call_sid", "")
    watch_url = lab_url + (data.get("watch_url") or f"/calls/{call_sid}")

    # If this run originated from WhatsApp, register the pending callback so the
    # summary gets routed back to the same chat once the call ends.
    wa_phone = WHATSAPP_ORIGIN.get()
    if wa_phone and call_sid:
        try:
            record_pending_call(
                call_sid=call_sid,
                business_id=business_id,
                user_id=user_id,
                whatsapp_phone=wa_phone,
                purpose=purpose,
                target_phone=phone,
                target_name=contact_name or "there",
            )
            logger.info(f"[voice_tools] dial → call_sid={call_sid} pending WhatsApp reply to {wa_phone}")
        except Exception as e:
            logger.warning(f"[voice_tools] could not record pending callback: {e}")

    return {
        "ok":           True,
        "call_sid":     call_sid,
        "watch_url":    watch_url,
        "contact_id":   contact_id,
        "contact_name": contact_name or "there",
        "phone":        phone,
        "purpose":      purpose,
        "message":      (
            f"Calling {contact_name or 'the contact'} at {phone} now. "
            f"I'll send the summary back here when the call ends."
        ),
    }


register_tool(
    name="dial_contact",
    description=(
        "Place an outbound voice call (Vox) to a phone number and have the "
        "agent ask about a specific topic. Use this when the user explicitly "
        "asks to call someone — e.g. 'call +91 98765 43210 and ask about the "
        "delivery status'. The call cost is real money (Twilio + Groq + "
        "ElevenLabs) so only use when the user clearly requested a phone call. "
        "Returns immediately with a call_sid; the call summary is delivered "
        "asynchronously (mirrored to WhatsApp if invoked from WhatsApp, and "
        "always logged in the CRM)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "phone": {
                "type": "string",
                "description": (
                    "Target phone number. Prefer E.164 (e.g. +919876543210). "
                    "Bare 10-digit numbers are auto-prefixed with +91 (India)."
                ),
            },
            "purpose": {
                "type": "string",
                "description": (
                    "What the agent should ask / why we're calling. Keep it "
                    "short and concrete, e.g. 'ask about the status of order "
                    "INV-2087'. Max ~300 chars."
                ),
            },
            "contact_name": {
                "type": "string",
                "description": "Contact's name if the user mentioned one. Optional.",
            },
            "contact_id": {
                "type": "string",
                "description": (
                    "Existing CRM contact id, if the user is asking about a "
                    "specific known contact. Optional — leave blank to look up "
                    "by phone or auto-create."
                ),
            },
        },
        "required": ["phone", "purpose"],
    },
    handler=_dial_contact,
    summary_fn=lambda a: f"Vox call → {a.get('phone','?')}: {(a.get('purpose') or '')[:80]}",
)
