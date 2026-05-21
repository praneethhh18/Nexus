"""
Endpoints the voice agent (Vox) calls during a live call to take action
on behalf of the caller. These are the "function-calling tools" the LLM
invokes mid-conversation:

    POST /api/voice/agent/rag-query        Search the business KB
    POST /api/voice/agent/schedule-callback Create a CRM task
    POST /api/voice/agent/send-email       Queue an email to the contact

All endpoints require X-Voice-Callback-Secret header matching
VOICE_CALLBACK_SECRET env var (same auth as /api/voice/callback).
Empty secret = open access (dev mode).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from loguru import logger

router = APIRouter(tags=["voice-agent-tools"])


def _verify_secret(provided: Optional[str]) -> None:
    expected = os.getenv("VOICE_CALLBACK_SECRET", "")
    if expected and provided != expected:
        raise HTTPException(401, "bad voice agent secret")


# ── Tool 1: RAG query — search the business knowledge base ──────────
@router.post("/api/voice/agent/rag-query")
async def voice_agent_rag_query(
    request: Request,
    x_voice_callback_secret: Optional[str] = Header(None, alias="X-Voice-Callback-Secret"),
):
    """The voice agent's `lookup_business_info` tool calls this.
    Body: { business_id: str, query: str, top_k: int (optional, default 3) }
    Returns: { results: [{text, source}], formatted: str }
    """
    _verify_secret(x_voice_callback_secret)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "body must be JSON")

    query = (body.get("query") or "").strip()
    top_k = int(body.get("top_k") or 3)
    if not query:
        raise HTTPException(400, "query is required")

    try:
        from rag.retriever import retrieve
        result = retrieve(query, top_k=top_k)
    except Exception as e:
        logger.warning(f"[voice-agent-tools] RAG failed: {e}")
        return {"results": [], "formatted": "(no knowledge base configured yet)"}

    chunks = result.get("results", [])[:top_k]
    if not chunks:
        return {"results": [], "formatted": "(no relevant info found)"}

    # Plain-text format the LLM can quote back to the caller naturally.
    lines = []
    for i, c in enumerate(chunks, 1):
        text = (c.get("text") or "").strip().replace("\n", " ")[:300]
        src = c.get("source") or "(internal)"
        lines.append(f"[{i}] {text} (source: {src})")
    return {
        "results": chunks,
        "formatted": "\n".join(lines),
    }


# ── Tool 2: Schedule callback — create a CRM task for follow-up ─────
@router.post("/api/voice/agent/schedule-callback")
async def voice_agent_schedule_callback(
    request: Request,
    x_voice_callback_secret: Optional[str] = Header(None, alias="X-Voice-Callback-Secret"),
):
    """The voice agent's `schedule_callback` tool calls this.
    Body: {
      business_id: str,
      contact_id: str,
      when_iso: str (ISO 8601, e.g. '2026-05-09T15:30:00+05:30'),
      reason: str,
      call_sid: str,
    }
    Creates a Task in the CRM with type='callback'.
    """
    _verify_secret(x_voice_callback_secret)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "body must be JSON")

    business_id = body.get("business_id", "").strip()
    contact_id  = body.get("contact_id", "").strip()
    when_iso    = body.get("when_iso", "").strip()
    reason      = (body.get("reason") or "Voice agent — caller requested callback").strip()
    call_sid    = body.get("call_sid", "").strip()
    if not business_id or not when_iso:
        raise HTTPException(400, "business_id and when_iso are required")

    # Validate ISO format
    try:
        when_dt = datetime.fromisoformat(when_iso.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, f"when_iso must be valid ISO 8601, got {when_iso!r}")

    try:
        from api import tasks as _tasks
        task = _tasks.create_task(
            business_id=business_id,
            user_id="vox",  # synthetic user — Vox is the creator
            data={
                "title": f"Callback: {reason}"[:200],
                "description": (
                    f"Voice agent (Vox) scheduled a callback for "
                    f"{when_dt.isoformat()}. Reason: {reason}. "
                    f"Source call: {call_sid}."
                ),
                "due_date": when_dt.isoformat(),
                "contact_id": contact_id or None,
                "tags": "vox,callback",
                "priority": "high",
            },
        )
        logger.info(
            f"[voice-agent-tools] callback scheduled: task={task.get('id','?')} "
            f"contact={contact_id!r} when={when_iso} reason={reason!r}"
        )
        return {"ok": True, "task_id": task.get("id"), "scheduled_for": when_iso}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[voice-agent-tools] schedule_callback failed: {e}")
        raise HTTPException(500, f"could not schedule callback: {e}")


# ── Tool 3: Send email — queue a follow-up email to the contact ─────
@router.post("/api/voice/agent/send-email")
async def voice_agent_send_email(
    request: Request,
    x_voice_callback_secret: Optional[str] = Header(None, alias="X-Voice-Callback-Secret"),
):
    """The voice agent's `send_email_followup` tool calls this.
    Body: {
      business_id: str,
      contact_id: str,
      subject: str,
      body: str,
      call_sid: str,
    }
    Queues an email task or directly sends if email integration is configured.
    For now, creates a Task with type='send_email' so a human can review
    + send (safer default than auto-sending an LLM-generated email).
    """
    _verify_secret(x_voice_callback_secret)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "body must be JSON")

    business_id = payload.get("business_id", "").strip()
    contact_id  = payload.get("contact_id", "").strip()
    subject     = payload.get("subject", "").strip()
    email_body  = payload.get("body", "").strip()
    call_sid    = payload.get("call_sid", "").strip()
    if not business_id or not subject:
        raise HTTPException(400, "business_id and subject are required")

    try:
        from api import tasks as _tasks
        task = _tasks.create_task(
            business_id=business_id,
            user_id="vox",
            data={
                "title": f"Send email: {subject}"[:200],
                "description": (
                    f"Voice agent (Vox) wants to send this email after the call.\n\n"
                    f"To: contact {contact_id or '(unknown)'}\n"
                    f"Subject: {subject}\n\n"
                    f"---\n{email_body}\n---\n\n"
                    f"Source call: {call_sid}.\n"
                    f"REVIEW BEFORE SENDING — content was AI-generated."
                ),
                "due_date": datetime.now(timezone.utc).isoformat(),
                "contact_id": contact_id or None,
                "tags": "vox,email",
                "priority": "normal",
            },
        )
        logger.info(
            f"[voice-agent-tools] email queued: task={task.get('id','?')} "
            f"contact={contact_id!r} subject={subject!r}"
        )
        return {"ok": True, "task_id": task.get("id"), "queued": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[voice-agent-tools] send_email failed: {e}")
        raise HTTPException(500, f"could not queue email: {e}")


# ── Tool 4: Contact context — pre-call brief for the voice agent ─────
@router.post("/api/voice/agent/contact-context")
async def voice_agent_contact_context(
    request: Request,
    x_voice_callback_secret: Optional[str] = Header(None, alias="X-Voice-Callback-Secret"),
):
    """
    Returns everything the voice agent needs to sound informed at the
    start of a call. Without this, Vox treats every caller as a cold
    lead and produces generic, robotic dialogue.

    Body: { business_id: str, contact_id: str }
    Returns: {
      contact: { first_name, last_name, email, phone, title, company_name, source },
      relationship: "customer" | "lead" | "unknown",
      open_deals: [{ name, stage, value, currency }],
      won_deals_count: int,
      recent_interactions: [{ type, subject, summary, when }],
      tags: [str],
      brief: str    # one-paragraph human-readable summary for the system prompt
    }
    """
    _verify_secret(x_voice_callback_secret)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "body must be JSON")

    business_id = (body.get("business_id") or "").strip()
    contact_id  = (body.get("contact_id") or "").strip()
    if not business_id or not contact_id:
        raise HTTPException(400, "business_id and contact_id are required")

    # Aggregate the pieces. Each lookup is best-effort — if any one fails
    # the agent still gets partial context rather than a hard error.
    contact: dict = {}
    open_deals: list[dict] = []
    won_deals_count = 0
    interactions: list[dict] = []
    tags: list[str] = []

    try:
        from api import crm as _crm
        contact = _crm.get_contact(business_id, contact_id) or {}
    except Exception as e:
        logger.warning(f"[contact-context] get_contact failed: {e}")

    try:
        from api import crm as _crm
        all_deals = _crm.list_deals(business_id, contact_id=contact_id, limit=20)
        for d in all_deals:
            if d.get("stage") == "won":
                won_deals_count += 1
            else:
                open_deals.append({
                    "name":     d.get("name"),
                    "stage":    d.get("stage"),
                    "value":    d.get("value"),
                    "currency": d.get("currency"),
                })
    except Exception as e:
        logger.warning(f"[contact-context] list_deals failed: {e}")

    try:
        from api import crm as _crm
        ints = _crm.list_interactions(business_id, contact_id=contact_id, limit=5)
        for i in ints:
            interactions.append({
                "type":    i.get("type"),
                "subject": (i.get("subject") or "")[:120],
                "summary": (i.get("summary") or "")[:300],
                "when":    i.get("created_at"),
            })
    except Exception as e:
        logger.warning(f"[contact-context] list_interactions failed: {e}")

    try:
        from api import tags as _tg
        tag_objs = _tg.tags_for(business_id, "contact", contact_id)
        tags = [t.get("name") for t in tag_objs if t.get("name")]
    except Exception as e:
        logger.warning(f"[contact-context] tags_for failed: {e}")

    relationship = "unknown"
    if won_deals_count > 0:
        relationship = "customer"
    elif open_deals or interactions:
        relationship = "lead"

    # Build a one-paragraph brief the voice agent can paste into its
    # system prompt. Kept under ~600 chars so it doesn't blow context.
    name = (
        f"{(contact.get('first_name') or '').strip()} "
        f"{(contact.get('last_name') or '').strip()}"
    ).strip() or "(unknown)"
    parts = [f"Caller: {name}"]
    if contact.get("title"):
        parts.append(f"role {contact['title']}")
    if contact.get("company_name"):
        parts.append(f"at {contact['company_name']}")
    parts.append(f"relationship: {relationship}")
    if won_deals_count:
        parts.append(f"{won_deals_count} won deal{'s' if won_deals_count != 1 else ''}")
    if open_deals:
        parts.append(
            f"{len(open_deals)} open deal{'s' if len(open_deals) != 1 else ''} "
            f"({', '.join(d['name'] or '?' for d in open_deals[:3])})"
        )
    if interactions:
        last = interactions[0]
        when = (last.get("when") or "")[:10]
        parts.append(
            f"last interaction: {last.get('type','note')} on {when} — "
            f"{(last.get('subject') or last.get('summary') or '')[:80]}"
        )
    if tags:
        parts.append(f"tags: {', '.join(tags[:5])}")
    brief = " · ".join(parts)[:600]

    return {
        "contact":             contact,
        "relationship":        relationship,
        "open_deals":          open_deals,
        "won_deals_count":     won_deals_count,
        "recent_interactions": interactions,
        "tags":                tags,
        "brief":               brief,
    }
