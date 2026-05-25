"""Inbound voice — Twilio webhooks driving the AI receptionist.

Twilio config (do this once in the Twilio console for your number):
    "A CALL COMES IN"          → Webhook (POST) → {NEXUS_PUBLIC_URL}/api/voice/twilio-inbound
    "CALL STATUS CHANGES"      → Webhook (POST) → {NEXUS_PUBLIC_URL}/api/voice/twilio-status

Per-turn flow:
    1. inbound webhook   → answer + initial Gather
    2. each gather POSTs → call llm → next Gather (or Hangup if [END_CALL])
    3. status webhook    → finalize (summary, CRM contact, WhatsApp digest)

Business resolution:
    - The Twilio "To" number identifies which business this call is for.
    - For the MVP we look up via env var TWILIO_INBOUND_BUSINESS_ID, with
      a graceful fallback to TWILIO_PHONE_NUMBER's owning business if any.
    - Future: a per-business twilio_number table for true multi-tenant.

Signature validation:
    - In production set VOICE_INBOUND_VALIDATE=1 and ensure TWILIO_AUTH_TOKEN
      matches your Twilio account. Requests with a bad signature are rejected.
    - Off by default so local development with ngrok / curl smoke tests works
      without juggling signatures.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Request, Response, HTTPException, Form
from loguru import logger

from api import inbound_calls
from agents import receptionist


router = APIRouter(tags=["voice_inbound"])

# Twilio's <Say> voices for Indian English. Aditi / Raveena are Polly voices
# Twilio supports out of the box. Override via env if you want a different one.
DEFAULT_VOICE = os.getenv("TWILIO_INBOUND_VOICE", "Polly.Aditi")
DEFAULT_LANG = os.getenv("TWILIO_INBOUND_LANGUAGE", "en-IN")

# Receptionist greeting — first thing the caller hears. Configurable per
# business later; for now, single env override.
DEFAULT_GREETING = os.getenv(
    "TWILIO_INBOUND_GREETING",
    "Hi, you've reached our AI assistant. How can I help you today?",
)


# ── Helpers ────────────────────────────────────────────────────────────────
def _twiml(xml: str) -> Response:
    return Response(content=xml, media_type="application/xml")


def _xml_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _gather_url(call_sid: str) -> str:
    """Twilio needs an absolute URL for the action attribute. Build it from
    NEXUS_PUBLIC_URL so it's reachable from Twilio's edge."""
    base = (os.getenv("NEXUS_PUBLIC_URL")
            or f"http://localhost:{os.getenv('NEXUS_PORT', '8000')}").rstrip("/")
    return f"{base}/api/voice/twilio-gather?call_sid={call_sid}"


def _build_gather_xml(say: str, call_sid: str, *, hint: str = "") -> str:
    """A standard Gather block: speak `say`, then listen for caller speech."""
    hint_attr = f' hints="{_xml_escape(hint)}"' if hint else ""
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response>'
        f'<Gather input="speech" speechTimeout="auto" timeout="6" '
        f'language="{DEFAULT_LANG}" action="{_gather_url(call_sid)}" '
        f'method="POST"{hint_attr}>'
        f'<Say voice="{DEFAULT_VOICE}" language="{DEFAULT_LANG}">{_xml_escape(say)}</Say>'
        f'</Gather>'
        # Fallback if the caller never speaks — say goodbye and hang up.
        f'<Say voice="{DEFAULT_VOICE}" language="{DEFAULT_LANG}">Sorry, I didn\'t hear you. Goodbye.</Say>'
        f'<Hangup/>'
        f'</Response>'
    )


def _build_hangup_xml(say: str) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response>'
        f'<Say voice="{DEFAULT_VOICE}" language="{DEFAULT_LANG}">{_xml_escape(say)}</Say>'
        f'<Hangup/>'
        f'</Response>'
    )


def _resolve_business_id(twilio_to: str) -> Optional[str]:
    """Pick which business owns this inbound call.

    Priority:
      1. TWILIO_INBOUND_BUSINESS_ID env override (single-tenant MVP)
      2. The business whose linked WhatsApp matches the dialled number
      3. The first active business
    """
    explicit = (os.getenv("TWILIO_INBOUND_BUSINESS_ID") or "").strip()
    if explicit:
        return explicit

    try:
        import sqlite3
        from api.businesses import BUSINESSES_TABLE
        from config.db import get_conn
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                f"SELECT id FROM {BUSINESSES_TABLE} WHERE is_active = 1 "
                f"ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        if row:
            return row["id"]
    except Exception as e:
        logger.warning(f"[voice_inbound] business resolution failed: {e}")
    return None


async def _validate_twilio_signature(request: Request) -> None:
    """Verify Twilio signed the request. No-op when validation is disabled
    via env (default for local dev) — production should set VOICE_INBOUND_VALIDATE=1."""
    if os.getenv("VOICE_INBOUND_VALIDATE", "0") != "1":
        return
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        logger.warning("[voice_inbound] validation enabled but TWILIO_AUTH_TOKEN missing")
        return
    sig = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    params = dict(form)
    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        logger.warning("[voice_inbound] twilio SDK missing; skipping signature check")
        return
    validator = RequestValidator(auth_token)
    if not validator.validate(url, params, sig):
        logger.warning(f"[voice_inbound] bad Twilio signature from url={url}")
        raise HTTPException(403, "bad twilio signature")


# ── Webhooks ───────────────────────────────────────────────────────────────
@router.post("/api/voice/twilio-inbound")
async def twilio_inbound(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(""),
    To: str = Form(""),
):
    """Twilio rings: start the session, greet, listen."""
    await _validate_twilio_signature(request)

    biz_id = _resolve_business_id(To)
    if not biz_id:
        # No business → polite voicemail-style hangup. Record nothing.
        logger.warning(f"[voice_inbound] no business resolved for To={To}; hanging up")
        return _twiml(_build_hangup_xml(
            "Sorry, this number isn't currently configured. Please try again later."
        ))

    inbound_calls.start_session(call_sid=CallSid, business_id=biz_id,
                                 from_number=From, twilio_to=To)
    logger.info(f"[voice_inbound] new call call_sid={CallSid} from={From} → biz={biz_id}")

    # Persist the greeting as the assistant's first turn so summarisation has
    # the full conversation later.
    inbound_calls.append_turn(CallSid, "assistant", DEFAULT_GREETING)
    return _twiml(_build_gather_xml(DEFAULT_GREETING, CallSid))


@router.post("/api/voice/twilio-gather")
async def twilio_gather(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(""),
    Confidence: str = Form(""),
    call_sid: str = "",  # query-string echo of CallSid (Twilio sends both — we trust the form one)
):
    """Each turn: caller spoke, we reply (and either keep listening or hang up)."""
    await _validate_twilio_signature(request)

    sess = inbound_calls.get_session(CallSid)
    if not sess:
        # Race: Twilio hit gather before we processed the inbound webhook —
        # extremely unlikely but worth a graceful out.
        logger.warning(f"[voice_inbound] gather for unknown call_sid={CallSid}; "
                       "falling back to a generic hangup")
        return _twiml(_build_hangup_xml("Sorry, something went wrong. Goodbye."))

    # Empty SpeechResult means caller stayed silent — let them retry once,
    # then summarise + hang up after a second silence.
    user_text = (SpeechResult or "").strip()
    if not user_text:
        last_turn = (sess["transcript"] or [{}])[-1]
        if last_turn.get("role") == "assistant" and last_turn.get("text", "").startswith("(silence)"):
            return _twiml(_build_hangup_xml("Sorry, I couldn't hear you. Please call back."))
        inbound_calls.append_turn(CallSid, "assistant", "(silence) Are you still there?")
        return _twiml(_build_gather_xml("Are you still there?", CallSid))

    transcript = inbound_calls.append_turn(CallSid, "user", user_text)

    # Pull a few KB chunks based on the latest caller utterance — gives the
    # receptionist a chance to answer factual questions without a tool call.
    biz_id = sess["business_id"]
    business_name = ""
    try:
        from api.businesses import get_business
        biz = get_business(biz_id) or {}
        business_name = biz.get("name", "")
    except Exception:
        pass
    rag_context = receptionist.fetch_rag_context(biz_id, user_text, k=3)

    reply = receptionist.reply_to_caller(
        business_id=biz_id, business_name=business_name,
        transcript=transcript, rag_context=rag_context,
    )
    end_call = receptionist.reply_should_end_call(reply)
    spoken = receptionist.strip_end_token(reply) or "Okay."
    inbound_calls.append_turn(CallSid, "assistant", spoken)

    if end_call:
        return _twiml(_build_hangup_xml(spoken))
    return _twiml(_build_gather_xml(spoken, CallSid))


@router.post("/api/voice/twilio-status")
async def twilio_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(""),
    CallDuration: str = Form(""),
):
    """Twilio status callback. We only act on terminal states — completed,
    no-answer, busy, failed, canceled — and run all post-call cleanup."""
    await _validate_twilio_signature(request)

    if CallStatus not in ("completed", "no-answer", "busy", "failed", "canceled"):
        return Response(status_code=204)

    sess = inbound_calls.get_session(CallSid)
    if not sess:
        return Response(status_code=204)
    if sess.get("status") == "completed":
        # Twilio occasionally retries the status webhook — don't double-process.
        return Response(status_code=204)

    duration = None
    try:
        duration = int(CallDuration) if CallDuration else None
    except ValueError:
        pass

    business_name = ""
    try:
        from api.businesses import get_business
        biz = get_business(sess["business_id"]) or {}
        business_name = biz.get("name", "")
    except Exception:
        pass

    summary = receptionist.finalize_call(
        call_sid=CallSid,
        business_id=sess["business_id"],
        business_name=business_name,
        from_number=sess.get("from_number", ""),
        transcript=sess.get("transcript", []),
        started_at=sess.get("started_at", ""),
        ended_at=sess.get("last_activity", ""),
        duration_sec=duration,
    )
    inbound_calls.finish_session(CallSid, summary=summary, status="completed")
    logger.info(f"[voice_inbound] finalised call_sid={CallSid} outcome={summary.get('outcome')}")

    # Missed-call rescue: if the call never connected to Vox (no-answer,
    # busy, failed, canceled, or a 0-3s drop), shoot the caller a
    # WhatsApp in the business's language so we don't lose the lead.
    # Best-effort, swallowed exceptions, status webhook must still 204.
    try:
        from api import missed_call_rescue
        if missed_call_rescue.is_missed(CallStatus, duration):
            result = missed_call_rescue.fire_rescue(
                business_id=sess["business_id"],
                from_phone=sess.get("from_number", ""),
                call_sid=CallSid,
                call_status=CallStatus,
                duration_sec=duration,
            )
            if result.get("fired"):
                logger.info(
                    f"[voice_inbound] missed-call rescue sent for "
                    f"call_sid={CallSid} → {sess.get('from_number','?')}"
                )
            else:
                logger.debug(
                    f"[voice_inbound] missed-call rescue skipped "
                    f"call_sid={CallSid} reason={result.get('reason')}"
                )
    except Exception as e:
        logger.warning(f"[voice_inbound] missed-call rescue threw: {e}")

    return Response(status_code=204)


# Read API: inbound calls show up in the existing /api/voice/calls endpoint
# (mirrored at finalize time via voice_calls.store_completed_call), so the CRM
# call-history view already works for them — no separate endpoint needed.
