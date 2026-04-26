"""
Email-triage IMAP account management + on-demand run + audit log.

The triage agent reads new mail every 15 minutes (see scheduler), classifies
each message, and queues reply drafts for approval. This router exposes the
admin surface: connect/disconnect the IMAP account, kick off a manual run,
and inspect the recent processing log.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context
from agents import email_triage as _email_triage

router = APIRouter(tags=["email_triage"])


@router.get("/api/email-triage/account")
def email_triage_account(ctx: dict = Depends(get_current_context)):
    return _email_triage.get_account(ctx["business_id"]) or {"connected": False}


@router.post("/api/email-triage/account")
def save_email_triage_account(body: dict, ctx: dict = Depends(get_current_context)):
    # Only owner/admin can configure the shared inbox
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can configure email triage")
    return _email_triage.save_account(
        business_id=ctx["business_id"],
        imap_host=(body.get("imap_host") or "").strip(),
        imap_port=int(body.get("imap_port", 993)),
        username=(body.get("username") or "").strip(),
        password=body.get("password") or "",
        folder=(body.get("folder") or "INBOX"),
        enabled=bool(body.get("enabled", True)),
        auto_draft_reply=bool(body.get("auto_draft_reply", True)),
    )


@router.delete("/api/email-triage/account")
def delete_email_triage_account(ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can disconnect email triage")
    _email_triage.disconnect_account(ctx["business_id"])
    return {"ok": True}


@router.post("/api/email-triage/run")
def run_email_triage(ctx: dict = Depends(get_current_context)):
    return _email_triage.run_for_business(ctx["business_id"])


@router.get("/api/email-triage/log")
def email_triage_log(limit: int = 50, ctx: dict = Depends(get_current_context)):
    return _email_triage.get_recent_log(ctx["business_id"], limit=limit)
