"""Inbound voice receptionist — the brain behind /api/voice/twilio-* webhooks.

Two responsibilities:

1. Per-turn reply (`reply_to_caller`) — generate ONE short response (1-2
   sentences) for Twilio to play. Latency-sensitive: must return in well
   under Twilio's 10-second gather timeout. We do NOT call tools during a
   turn — keeps latency low and avoids long pauses on the call. RAG context
   is injected into the prompt so the receptionist can answer FAQs from the
   knowledge base without a tool round-trip.

2. Post-call processing (`finalize_call`) — fired from the Twilio status
   webhook when the call hangs up. Summarises the transcript, extracts the
   caller's intent, creates/updates a CRM contact, logs an interaction,
   mirrors a row to nexus_voice_calls, and pushes a WhatsApp digest to the
   linked owner. All best-effort — failures here never affect the call.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Per-turn reply ──────────────────────────────────────────────────────────
def reply_to_caller(*, business_id: str, business_name: str,
                     transcript: List[Dict[str, str]], rag_context: str = "") -> str:
    """Return the receptionist's next utterance. Always 1-2 sentences."""
    from config import llm_provider

    # Compress transcript for the prompt — recent turns matter most
    recent = transcript[-12:] if len(transcript) > 12 else transcript
    convo_lines = []
    for t in recent:
        who = "Caller" if t.get("role") == "user" else "You"
        text = (t.get("text") or "").strip()
        if text:
            convo_lines.append(f"{who}: {text}")
    convo = "\n".join(convo_lines)

    rag_block = ""
    if rag_context.strip():
        rag_block = (
            f"\n\nKnowledge base context (use this to answer factual questions; "
            f"don't quote prices unless they're in this context):\n{rag_context.strip()[:1500]}"
        )

    system = (
        f"You are the AI voice receptionist for {business_name or 'this business'}. "
        f"You are on a phone call right now. Rules:\n"
        f"- Reply in 1-2 short sentences max. This is voice, not chat.\n"
        f"- Be warm but efficient. The caller's time matters.\n"
        f"- Capture: their name (if not given), what they want, urgency.\n"
        f"- Don't make up facts or prices. If unsure, say 'let me have someone "
        f"call you back about that — what's the best time?'\n"
        f"- If the caller seems frustrated or asks for a human, say "
        f"'absolutely — I'll have the team call you within 30 minutes' and "
        f"end the call.\n"
        f"- End the call when the caller has clearly said goodbye, or when "
        f"you've captured their need and confirmed a next step. "
        f"Signal end-of-call by adding the literal token [END_CALL] at the end "
        f"of your reply (the system will hang up after speaking your line)."
        f"{rag_block}"
    )

    prompt = (
        f"Conversation so far:\n{convo}\n\n"
        f"What do you say next? Reply in 1-2 short sentences. "
        f"Add [END_CALL] at the end if the conversation should end now."
    )

    try:
        # Voice replies ARE complex — drafting a coherent natural response —
        # so we want cloud LLM if available. force_cloud=True bypasses the
        # router; the conversation cap still gates it.
        text = llm_provider.invoke(prompt, system=system, max_tokens=220,
                                    temperature=0.5, force_cloud=True)
    except Exception as e:
        logger.warning(f"[receptionist] LLM call failed: {e}")
        text = "I'm having trouble right now. Let me have the team call you back. [END_CALL]"

    return (text or "").strip()


def reply_should_end_call(reply: str) -> bool:
    """True if the LLM signalled hang-up via the [END_CALL] sentinel."""
    return "[END_CALL]" in (reply or "").upper()


def strip_end_token(reply: str) -> str:
    """Remove the [END_CALL] sentinel before sending text to TTS."""
    return re.sub(r"\s*\[END_CALL\]\s*", "", reply or "", flags=re.IGNORECASE).strip()


# ── Knowledge-base lookup for the receptionist ──────────────────────────────
def fetch_rag_context(business_id: str, query: str, k: int = 3) -> str:
    """Pull a few relevant chunks from the business's knowledge base."""
    if not query.strip():
        return ""
    try:
        from rag import retriever
        hits = retriever.retrieve(business_id, query, k=k) or []
        chunks = []
        for h in hits[:k]:
            text = (h.get("text") or h.get("content") or "").strip()
            if text:
                chunks.append(text[:600])
        return "\n\n---\n\n".join(chunks)
    except Exception as e:
        logger.debug(f"[receptionist] RAG lookup failed (non-fatal): {e}")
        return ""


# ── Post-call processing ────────────────────────────────────────────────────
_SUMMARY_SCHEMA_HINT = (
    'Respond ONLY with valid JSON in this shape: '
    '{"caller_name": str|null, "intent": str, "outcome": '
    '"interested"|"info_request"|"complaint"|"callback_requested"|'
    '"booking"|"spam"|"other", '
    '"urgency": "high"|"medium"|"low", '
    '"next_step": str, "headline": str, '
    '"sentiment": "positive"|"neutral"|"negative"}'
)


def summarize_call(transcript: List[Dict[str, str]],
                    business_name: str) -> Dict[str, Any]:
    """LLM-based post-call summarisation. Best-effort; falls back to a
    hand-built dict if parsing fails so we never lose a call's record."""
    from config import llm_provider

    convo_lines = []
    for t in transcript:
        who = "Caller" if t.get("role") == "user" else "Receptionist"
        text = (t.get("text") or "").strip()
        if text:
            convo_lines.append(f"{who}: {text}")
    convo = "\n".join(convo_lines)

    system = (
        f"You are summarising an inbound phone call to {business_name}. "
        f"Extract structured data the business owner can act on. "
        f"{_SUMMARY_SCHEMA_HINT}"
    )
    prompt = f"Transcript:\n{convo}\n\nSummarise as JSON only."

    try:
        # Call transcript + caller name = PII. Route through Privacy Bridge
        # when configured so the customer's call data stays on their laptop.
        raw = llm_provider.invoke(prompt, system=system, max_tokens=400,
                                   temperature=0.1, sensitive=True)
        # Trim common LLM wrappers (```json ... ```)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip(),
                     flags=re.MULTILINE)
        data = json.loads(raw)
        # Validate / normalise keys
        return {
            "caller_name": data.get("caller_name"),
            "intent":      (data.get("intent") or "").strip()[:300],
            "outcome":     (data.get("outcome") or "other").strip(),
            "urgency":     (data.get("urgency") or "medium").strip(),
            "next_step":   (data.get("next_step") or "").strip()[:300],
            "headline":    (data.get("headline") or "").strip()[:200],
            "sentiment":   (data.get("sentiment") or "neutral").strip(),
        }
    except Exception as e:
        logger.warning(f"[receptionist] summary parse failed: {e}; using fallback")
        first_user = next((t.get("text") for t in transcript if t.get("role") == "user"), "")
        return {
            "caller_name": None,
            "intent":      first_user[:300] or "Unknown — see full transcript",
            "outcome":     "other",
            "urgency":     "medium",
            "next_step":   "Review transcript and follow up.",
            "headline":    f"Inbound call ({len(transcript)} turns)",
            "sentiment":   "neutral",
        }


def finalize_call(*, call_sid: str, business_id: str, business_name: str,
                   from_number: str, transcript: List[Dict[str, str]],
                   started_at: str, ended_at: str,
                   duration_sec: Optional[int] = None) -> Dict[str, Any]:
    """Run all post-call cleanup. Returns the summary dict for logging."""
    summary = summarize_call(transcript, business_name)

    # 1. Find or create a CRM contact for the caller's number
    contact_id: Optional[str] = None
    try:
        contact_id = _find_or_create_contact(business_id, from_number,
                                              summary.get("caller_name"))
    except Exception as e:
        logger.warning(f"[receptionist] contact upsert failed: {e}")

    # 2. Mirror to the unified voice_calls table so it shows up in the same
    #    history view as outbound calls, no parallel UI needed.
    try:
        from api import voice_calls
        voice_calls.store_completed_call({
            "call_sid":     call_sid,
            "business_id":  business_id,
            "contact_id":   contact_id or "",
            "started_at":   started_at,
            "ended_at":     ended_at,
            "duration_sec": duration_sec,
            "summary":      summary,
            "turns":        transcript,
            "watch_url":    "",  # no lab cockpit for inbound
        }, created_by="receptionist")
    except Exception as e:
        logger.warning(f"[receptionist] voice_calls.store failed: {e}")

    # 3. Distil per-contact memory so future interactions have context.
    if contact_id:
        try:
            from api import contact_memory
            contact_memory.auto_extract_from_call(
                business_id=business_id, contact_id=contact_id,
                call_sid=call_sid, transcript=transcript, summary=summary,
            )
        except Exception as e:
            logger.warning(f"[receptionist] per-contact memory extract failed: {e}")

    # 4. If the owner has a linked WhatsApp number, push the digest
    try:
        _push_whatsapp_digest(business_id, from_number, summary, duration_sec)
    except Exception as e:
        logger.warning(f"[receptionist] WhatsApp digest push failed: {e}")

    return summary


def _find_or_create_contact(business_id: str, phone: str,
                              name: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    from api import crm as _crm
    last10 = re.sub(r"\D", "", phone)[-10:]
    if last10:
        for c in _crm.list_contacts(business_id, search=last10, limit=10):
            digits = re.sub(r"\D", "", c.get("phone") or "")
            if digits.endswith(last10):
                return c.get("id")
    nm = (name or "").strip() or "Inbound caller"
    parts = nm.split(" ", 1)
    payload = {
        "first_name": parts[0],
        "last_name":  parts[1] if len(parts) > 1 else None,
        "phone":      phone,
        "source":     "inbound-call",
        "tags":       "inbound-caller",
    }
    return _crm.create_contact(business_id, "system", payload).get("id")


def _push_whatsapp_digest(business_id: str, from_number: str,
                           summary: Dict[str, Any],
                           duration_sec: Optional[int]) -> None:
    """Send the call summary back to the business owner's WhatsApp."""
    from api.whatsapp import get_linked_phone, send_outbound
    owner_phone = get_linked_phone(business_id)
    if not owner_phone:
        return  # owner hasn't linked WhatsApp; skip silently

    caller = summary.get("caller_name") or from_number or "an unknown number"
    lines = [
        f"📞 Inbound call from *{caller}* ({from_number})",
        "",
        f"*Outcome:* {summary.get('outcome','—')}",
        f"*Intent:* {summary.get('intent','—')}",
    ]
    if summary.get("next_step"):
        lines.append(f"*Next step:* {summary['next_step']}")
    if summary.get("urgency") in ("high",):
        lines.append("⚠️ *Urgent — caller asked for a fast response*")
    if duration_sec:
        m, s = divmod(int(duration_sec), 60)
        lines.append(f"_Duration: {m}m {s}s · logged in CRM._")
    else:
        lines.append("_Logged in CRM._")
    send_outbound(owner_phone, "\n".join(lines))
