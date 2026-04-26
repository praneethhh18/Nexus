"""
WhatsApp link flow + bridge webhook.

Per-user link: the user generates a 6-char code, texts it to the bot,
and the local Node bridge calls back here to attach their phone number
to their account. Inbound messages and attachment fetches both come
from the bridge protected by `X-Nexus-Secret`.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from api.auth import get_current_context, get_current_user
from api import whatsapp as _wa

router = APIRouter(tags=["whatsapp"])


@router.post("/api/whatsapp/link/generate")
def whatsapp_generate_link(ctx: dict = Depends(get_current_context)):
    """Issue a 6-char code the user will text to the WhatsApp bot to link their phone."""
    return _wa.generate_link_token(ctx["user"]["id"], ctx["business_id"])


@router.get("/api/whatsapp/account")
def whatsapp_account(ctx: dict = Depends(get_current_context)):
    acc = _wa.get_account_for_user(ctx["user"]["id"])
    return acc or {"linked": False}


@router.delete("/api/whatsapp/account")
def whatsapp_unlink(ctx: dict = Depends(get_current_context)):
    _wa.unlink_account(ctx["user"]["id"])
    return {"ok": True}


@router.get("/api/whatsapp/bridge-secret")
def whatsapp_bridge_secret(user: dict = Depends(get_current_user)):
    """The shared secret the Node bridge needs. Owner/admin only."""
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return {"secret": _wa.get_bridge_secret()}


@router.post("/api/whatsapp/inbound")
async def whatsapp_inbound(request: Request):
    """
    Receive an incoming WhatsApp message from the local Node bridge.
    Protected by X-Nexus-Secret header (the same value the bridge reads from
    its .env). Returns a JSON reply the bridge sends back over WhatsApp.
    """
    secret = request.headers.get("X-Nexus-Secret", "")
    _wa.verify_bridge_secret(secret)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    phone = (body.get("from") or "").strip()
    text = (body.get("text") or "").strip()
    message_id = (body.get("message_id") or "").strip()

    if len(text) > 4000:
        text = text[:4000]

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: _wa.handle_inbound(phone, text, message_id),
    )
    return result


@router.get("/api/whatsapp/attachment")
def whatsapp_attachment(path: str, request: Request):
    """
    Serve a generated file to the bridge so it can forward it over WhatsApp.
    Protected by X-Nexus-Secret. Only files inside outputs/ are served.
    """
    _wa.verify_bridge_secret(request.headers.get("X-Nexus-Secret", ""))

    from config.settings import OUTPUTS_DIR
    try:
        absolute = Path(path).resolve()
        absolute.relative_to(Path(OUTPUTS_DIR).resolve())
    except (ValueError, OSError):
        raise HTTPException(400, "Path outside of outputs/")
    if not absolute.is_file():
        raise HTTPException(404, "File not found")

    ext = absolute.suffix.lower()
    mime = "application/pdf" if ext == ".pdf" \
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
        if ext == ".docx" else "application/octet-stream"
    return FileResponse(str(absolute), filename=absolute.name, media_type=mime)
