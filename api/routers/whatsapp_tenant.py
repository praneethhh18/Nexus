"""Multi-tenant WhatsApp connection API — each NexusAgent business links
their own WhatsApp number via a QR scan from the in-app Settings page.

Flow:
    1. Customer clicks "Connect WhatsApp" in Settings
       → POST /api/whatsapp/tenant/connect
       → Backend tells the Node bridge to start a Baileys instance for
         their business_id. Bridge generates a QR and returns it.
    2. Frontend polls GET /api/whatsapp/tenant/status every 2s.
       → Backend forwards to bridge → returns QR + status.
       → Frontend renders the QR as an image.
    3. Customer scans QR with their phone.
       → Bridge connection.update fires with 'open'.
       → Status flips to "connected" with profile.phone.
       → Frontend stops polling.
    4. Inbound messages from their leads arrive at the bridge → forwarded
       to /api/whatsapp/inbound with `business_id` in the payload → routed
       to the correct tenant in the existing inbound handler.

Plan gate: Starter+ (Free tier doesn't get WhatsApp at all per PLANS).

Bridge URL: configured via `WA_BRIDGE_URL` env (default
`http://127.0.0.1:3001`). Auth: `X-Nexus-Secret` header — same shared
secret the legacy bridge endpoints already use.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth import get_current_context
from api.plan_gate import require_plan

router = APIRouter(tags=["whatsapp_tenant"])


def _bridge_url() -> str:
    return (os.getenv("WA_BRIDGE_URL") or "http://127.0.0.1:3001").rstrip("/")


def _bridge_secret() -> str:
    return (os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("NEXUS_WEBHOOK_SECRET") or "").strip()


def _bridge_headers() -> Dict[str, str]:
    secret = _bridge_secret()
    if not secret:
        raise HTTPException(
            503,
            "WhatsApp bridge not configured: set WHATSAPP_WEBHOOK_SECRET in .env "
            "and start the whatsapp_bridge process.",
        )
    return {"X-Nexus-Secret": secret, "Content-Type": "application/json"}


async def _call_bridge(method: str, path: str, *, json_body: Any = None) -> Dict[str, Any]:
    """Tiny wrapper around httpx with consistent error mapping.
    503 if bridge unreachable; bubble bridge's own error otherwise."""
    url = f"{_bridge_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.request(
                method, url,
                headers=_bridge_headers(),
                json=json_body,
            )
    except httpx.RequestError as e:
        logger.warning(f"[wa-tenant] bridge unreachable at {url}: {e}")
        raise HTTPException(
            503,
            "WhatsApp bridge unreachable. Make sure whatsapp_bridge is running "
            "on port 3001 (cd whatsapp_bridge && npm start).",
        )
    if r.status_code >= 400:
        try:
            err = r.json().get("error") or r.text[:200]
        except Exception:
            err = r.text[:200]
        raise HTTPException(r.status_code, f"Bridge error: {err}")
    try:
        return r.json()
    except Exception:
        return {"ok": True}


# ── Endpoints ──────────────────────────────────────────────────────────────
@router.post("/api/whatsapp/tenant/connect")
async def connect(ctx: dict = Depends(get_current_context)):
    """Start a Baileys connection for the caller's business. Returns the
    bridge's initial snapshot (status + QR if already generated).

    Idempotent — if the business already has a connection in progress or
    is connected, returns the current state without creating a new one."""
    require_plan(ctx["business_id"], "starter")
    biz = ctx["business_id"]
    snap = await _call_bridge("POST", f"/tenant/{biz}/connect")
    logger.info(f"[wa-tenant] connect biz={biz} → status={snap.get('status')}")
    return snap


@router.get("/api/whatsapp/tenant/status")
async def status(ctx: dict = Depends(get_current_context)):
    """Get current connection state + QR (if pending). Frontend polls
    this every 2-3 sec while showing the QR modal. Returns:
        {
          business_id, status, qr (string or null), profile (or null),
          last_error, last_update
        }
    status enum: idle | connecting | qr_pending | connected
               | disconnected | logged_out
    """
    require_plan(ctx["business_id"], "starter")
    biz = ctx["business_id"]
    return await _call_bridge("GET", f"/tenant/{biz}/status")


@router.post("/api/whatsapp/tenant/disconnect")
async def disconnect(ctx: dict = Depends(get_current_context)):
    """Logout + wipe the per-business auth state. After this, the customer
    must scan QR again to reconnect (lets them switch to a different
    WhatsApp number cleanly)."""
    if ctx.get("business_role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can disconnect WhatsApp")
    biz = ctx["business_id"]
    res = await _call_bridge("POST", f"/tenant/{biz}/disconnect")
    logger.info(f"[wa-tenant] disconnect biz={biz}")
    return res
