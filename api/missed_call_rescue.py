"""Missed-call rescue: when an inbound call doesn't connect (no answer,
busy line, very-short drop), shoot a WhatsApp message to the caller
within seconds.

The bet: an Indian SMB owner loses 25-40% of inbound leads to missed
calls. A 60-second auto-reply is the difference between losing the
customer and booking the order.

Trigger surfaces:
    1. Inbound (Twilio) — voice_inbound.twilio_status fires us when
       CallStatus is no-answer / busy / failed / canceled, OR when
       duration is suspiciously short (caller hung up before we said
       hello).
    2. Outbound (Vox) — voice_callback can fire us when the call
       record's outcome is no_answer / failed.

What we do:
    * Resolve the caller's number against the CRM (existing contact
      vs. unknown).
    * Render a localized rescue message in the business's
      voice_language (en/hi/ta/mr).
    * Push to WhatsApp via the local bridge.
    * Log an interaction so it shows up on the contact timeline.
    * Create a follow-up task assigned to the business owner.

All side effects are best-effort. If WhatsApp delivery fails we log
and continue; we never break the parent call-finalization path.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, Optional

from loguru import logger


# CallStatus values that count as "missed". 'completed' with a tiny
# duration is also missed in spirit (caller hung up before connecting
# to Vox); the threshold is configurable.
MISSED_CALL_STATUSES = {"no-answer", "busy", "failed", "canceled", "no_answer"}
SHORT_CALL_THRESHOLD_SEC = 4   # under 4s the human didn't really land


# Rescue copy per language. Keep these short — WhatsApp opens look bad
# at multi-paragraph length and the goal is to feel like a person typed
# it. {biz} is the business name; {when} is a relative time.
RESCUE_TEMPLATES = {
    "en": (
        "Hi! This is {biz}. We just missed your call. "
        "Reply here and we'll get back to you in a few minutes — "
        "or share what you need and we'll be ready when we call back."
    ),
    "hi": (
        "Namaste! {biz} se message hai. Aapka call abhi miss ho gaya. "
        "Yahin reply kijiye, hum thodi der mein wapas call karenge — "
        "ya bata dijiye kya chahiye, hum tayyar ho jayenge."
    ),
    "ta": (
        "Vanakkam! Idhu {biz}. Ungal call konjam munnadi miss aagiduchu. "
        "Inga reply pannunga, naanga konja neram la wapasu call panrom — "
        "illana enna venum nu sollunga, naanga ready aa irukkom."
    ),
    "mr": (
        "Namaskar! He {biz} ahe. Tumcha call atta miss zhala. "
        "Ithech reply kara, amhi thodyaveles parat call karto — "
        "kinva kay pahije te sanga, amhi tayar hoto."
    ),
}


def is_missed(call_status: str, duration_sec: Optional[int]) -> bool:
    """The two ways a call counts as missed."""
    if (call_status or "").strip().lower() in MISSED_CALL_STATUSES:
        return True
    if duration_sec is not None and 0 <= duration_sec < SHORT_CALL_THRESHOLD_SEC:
        return True
    return False


def _normalize_phone(raw: str) -> str:
    """Twilio's `From` arrives as +91... or 91... — normalize to +E.164.
    The WhatsApp bridge accepts either form but we want the CRM lookup
    + the activity log to use a consistent shape."""
    s = re.sub(r"[^\d+]", "", raw or "")
    if not s:
        return ""
    if not s.startswith("+"):
        # Add country code only if it looks domestic; otherwise leave it.
        if s.startswith("91") and len(s) >= 12:
            s = "+" + s
        elif len(s) == 10:
            s = "+91" + s   # default India bias for SMB users
        else:
            s = "+" + s
    return s


def _resolve_contact(business_id: str, phone: str) -> Optional[Dict]:
    """Look up the caller in the CRM. Returns the row dict or None."""
    if not (business_id and phone):
        return None
    try:
        from api import crm as _crm
        candidates = _crm.list_contacts(business_id=business_id, limit=500) or []
    except Exception as e:
        logger.debug(f"[rescue] contact lookup failed: {e}")
        return None

    needle = re.sub(r"[^\d]", "", phone)[-10:]   # last 10 digits for India
    for c in candidates:
        p = re.sub(r"[^\d]", "", (c.get("phone") or ""))
        if p and p.endswith(needle):
            return c
    return None


def _business_voice_language(business_id: str) -> str:
    try:
        from api.businesses import get_business
        biz = get_business(business_id) or {}
        return (biz.get("voice_language") or "en").strip().lower()
    except Exception:
        return "en"


def _business_name(business_id: str) -> str:
    try:
        from api.businesses import get_business
        biz = get_business(business_id) or {}
        return (biz.get("name") or "our team").strip()
    except Exception:
        return "our team"


def _render_message(business_id: str) -> str:
    lang = _business_voice_language(business_id)
    template = RESCUE_TEMPLATES.get(lang) or RESCUE_TEMPLATES["en"]
    return template.format(biz=_business_name(business_id))


# ── Side effects ────────────────────────────────────────────────────────────
def _log_interaction(business_id: str, contact_id: Optional[str],
                      phone: str, message: str, call_sid: str) -> None:
    """Record the rescue as a CRM interaction so it shows up on the
    contact's timeline and the activity feed. Best-effort."""
    try:
        from api import crm as _crm
        _crm.create_interaction(
            business_id=business_id,
            user_id="vox",
            data={
                # Schema's INTERACTION_TYPES is ("call","email","meeting",
                # "note"); WhatsApp lives under 'note' until we widen the
                # enum. Subject line carries the channel cue.
                "type": "note",
                "subject": "WhatsApp rescue sent (missed call)",
                "summary": (
                    f"Auto-rescue WhatsApp sent to {phone} after missed call "
                    f"{call_sid or '(no sid)'}.\n\n-----\n{message}\n-----"
                ),
                "contact_id": contact_id,
            },
        )
    except Exception as e:
        logger.debug(f"[rescue] interaction log failed: {e}")


def _create_followup_task(business_id: str, contact_id: Optional[str],
                          phone: str, owner_id: Optional[str]) -> None:
    """Drop a task on the owner so the rescue WhatsApp doesn't fall
    through the cracks if the customer replies and nobody's watching."""
    if not owner_id:
        try:
            from api.businesses import get_business
            biz = get_business(business_id) or {}
            owner_id = biz.get("owner_id")
        except Exception:
            owner_id = None
    try:
        from api import tasks as _tasks
        _tasks.create_task(
            business_id=business_id,
            user_id=owner_id or "vox",
            data={
                "title": f"Missed-call rescue: follow up with {phone}",
                "description": (
                    "Auto-rescue WhatsApp was sent. Reply to the chat if "
                    "the customer responds, or call back if no reply by "
                    "end of day."
                ),
                "priority": "high",
                "status": "open",
                "due_date": datetime.now(timezone.utc).date().isoformat(),
                "contact_id": contact_id,
                "tags": "vox,missed-call",
                "assignee_id": owner_id,
            },
        )
    except Exception as e:
        logger.debug(f"[rescue] follow-up task creation failed: {e}")


# ── Public entry point ──────────────────────────────────────────────────────
def fire_rescue(
    business_id: str,
    from_phone: str,
    *,
    call_sid: str = "",
    call_status: str = "",
    duration_sec: Optional[int] = None,
) -> Dict:
    """Run the rescue pipeline for one missed call.

    Returns:
        {
          'fired': bool,        was a WhatsApp actually sent?
          'reason': str,        'sent' | 'not-missed' | 'no-phone' | 'wa-failed' | etc.
          'contact_id': str|None,
          'message': str,       what we sent (empty when fired=False)
        }
    """
    out = {"fired": False, "reason": "", "contact_id": None, "message": ""}

    if not is_missed(call_status, duration_sec):
        out["reason"] = "not-missed"
        return out

    phone = _normalize_phone(from_phone)
    if not phone:
        out["reason"] = "no-phone"
        return out

    contact = _resolve_contact(business_id, phone) or {}
    contact_id = contact.get("id")
    out["contact_id"] = contact_id

    # Render + send
    message = _render_message(business_id)
    out["message"] = message
    try:
        from api.whatsapp import send_outbound
        send_outbound(phone, message)
        out["fired"] = True
        out["reason"] = "sent"
        logger.info(
            f"[rescue] WhatsApp sent to {phone} for biz={business_id} "
            f"call_sid={call_sid} contact_id={contact_id}"
        )
    except Exception as e:
        out["reason"] = f"wa-failed: {e}"
        logger.warning(f"[rescue] WhatsApp send failed for {phone}: {e}")
        return out

    # Best-effort follow-ups (do NOT gate the return on these)
    _log_interaction(business_id, contact_id, phone, message, call_sid)
    _create_followup_task(business_id, contact_id, phone, owner_id=None)
    return out
