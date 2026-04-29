"""
SMTP router — per-workspace email send config + actually-send endpoint.

Surfaces:
  GET  /api/workspace/smtp        — read current config (no password)
  PUT  /api/workspace/smtp        — create/update; admin only
  POST /api/workspace/smtp/test   — verify creds against the SMTP server
  DELETE /api/workspace/smtp      — remove config
  POST /api/email/send            — send a real email via configured SMTP

Auth: workspace SMTP is admin/owner only since it's outbound-from-our-domain.
Sending is open to any workspace member (so reps can fire drafts).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from api import smtp_credentials as _smtp
from api.auth import get_current_context

router = APIRouter(tags=["smtp"])


def _require_admin(ctx: dict) -> None:
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can manage SMTP settings.")


# ── Config schema ───────────────────────────────────────────────────────────
class SmtpConfigIn(BaseModel):
    host: str = Field(..., min_length=1, max_length=200)
    port: int = Field(..., ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=200)
    # Password is optional on update — empty string keeps the stored value.
    password: str = Field(default="", max_length=400)
    from_email: EmailStr
    from_name: str = Field(default="", max_length=120)
    use_tls: bool = True


# ── Endpoints ───────────────────────────────────────────────────────────────
@router.get("/api/workspace/smtp")
def read_smtp(ctx: dict = Depends(get_current_context)):
    """Return current SMTP config or {configured: false}. Anyone in the
    workspace can see whether it's configured (so the UI knows whether
    to show "Send" vs "mailto" buttons), but only admins see/edit details."""
    cfg = _smtp.get_config(ctx["business_id"])
    if not cfg:
        return {"configured": False}
    is_admin = ctx["business_role"] in ("owner", "admin")
    base = {
        "configured": True,
        "from_email": cfg["from_email"],
        "from_name":  cfg.get("from_name") or "",
    }
    if is_admin:
        base.update({
            "host": cfg["host"],
            "port": cfg["port"],
            "username": cfg["username"],
            "use_tls":  bool(cfg.get("use_tls", True)),
            "updated_at": cfg.get("updated_at"),
        })
    return base


@router.put("/api/workspace/smtp")
def write_smtp(payload: SmtpConfigIn, ctx: dict = Depends(get_current_context)):
    _require_admin(ctx)
    try:
        cfg = _smtp.save_config(
            ctx["business_id"], ctx["user"]["id"],
            host=payload.host, port=payload.port,
            username=payload.username, password=payload.password,
            from_email=str(payload.from_email),
            from_name=payload.from_name, use_tls=payload.use_tls,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "config": cfg}


@router.delete("/api/workspace/smtp")
def remove_smtp(ctx: dict = Depends(get_current_context)):
    _require_admin(ctx)
    removed = _smtp.delete_config(ctx["business_id"])
    return {"ok": True, "removed": removed}


@router.post("/api/workspace/smtp/test")
def test_smtp(payload: Optional[SmtpConfigIn] = None,
              ctx: dict = Depends(get_current_context)):
    """Test SMTP credentials. If a payload is provided, test those values
    (admin only — common before saving). If not, test the stored config."""
    if payload:
        _require_admin(ctx)
        cfg = {
            "host": payload.host, "port": payload.port,
            "username": payload.username, "password": payload.password,
            "use_tls": payload.use_tls,
        }
        if not payload.password:
            # Reuse the stored password if they only edited host/port/etc.
            stored = _smtp.get_config(ctx["business_id"], include_password=True)
            if stored:
                cfg["password"] = stored.get("password", "")
        if not cfg.get("password"):
            raise HTTPException(400, "Password required to test SMTP.")
    else:
        cfg = _smtp.get_config(ctx["business_id"], include_password=True)
        if not cfg:
            raise HTTPException(400, "No SMTP configured to test.")

    return _smtp.test_connection(cfg)


# ── Send ────────────────────────────────────────────────────────────────────
class SendIn(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=400)
    body: str = Field(..., min_length=1, max_length=200_000)
    cc: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None


@router.post("/api/email/send")
def send_email(payload: SendIn, ctx: dict = Depends(get_current_context)):
    """Send via the workspace's SMTP. Any member can call; SMTP must be
    configured by an admin first."""
    try:
        return _smtp.send_email(
            ctx["business_id"],
            to=str(payload.to), subject=payload.subject, body=payload.body,
            cc=str(payload.cc) if payload.cc else None,
            reply_to=str(payload.reply_to) if payload.reply_to else None,
        )
    except _smtp.SmtpSendError as e:
        raise HTTPException(400, str(e))
