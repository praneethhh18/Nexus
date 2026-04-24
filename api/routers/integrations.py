"""
Integrations router — provider catalog + per-business connections +
generic inbound webhook receiver (3.4).
"""
from __future__ import annotations

import json as _json

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from api.auth import get_current_context

router = APIRouter(tags=["integrations"])


@router.get("/api/integrations/providers")
def integrations_providers(ctx: dict = Depends(get_current_context)):
    """Catalog of every shipped integration provider."""
    from api import integrations
    return {
        "providers": integrations.list_providers(),
        "categories": integrations.CATEGORY_LABELS,
    }


@router.get("/api/integrations")
def integrations_list(ctx: dict = Depends(get_current_context)):
    """Integrations connected for this business."""
    from api import integrations
    return integrations.list_connections(ctx["business_id"])


@router.post("/api/integrations/{provider}/connect")
def integrations_connect(provider: str, body: dict,
                         ctx: dict = Depends(get_current_context)):
    """Store connection config for a provider. Owner/admin only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can connect integrations")
    from api import integrations
    try:
        return integrations.connect(ctx["business_id"], provider, body or {})
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/integrations/{provider}")
def integrations_disconnect(provider: str,
                            ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can disconnect integrations")
    from api import integrations
    integrations.disconnect(ctx["business_id"], provider)
    return {"ok": True}


@router.post("/api/integrations/{provider}/ping")
def integrations_ping(provider: str, ctx: dict = Depends(get_current_context)):
    """Refresh health status for a connected integration."""
    from api import integrations
    return integrations.ping(ctx["business_id"], provider)


@router.post("/api/webhooks/{provider}")
async def generic_webhook_receiver(provider: str, request: Request):
    """
    Generic inbound webhook endpoint. Adapters register themselves by setting
    `nexus_integrations.config_json.webhook_secret` per business; the body is
    HMAC-verified against any signature header the provider sends (x-hub-
    signature-256 style), then stored in `nexus_notifications` as a record
    the user can review.

    The URL is `/api/webhooks/{provider}?business_id=...` — the business_id
    query param is REQUIRED since the request is unauthenticated.
    """
    from api import integrations, notifications
    business_id = request.query_params.get("business_id", "")
    if not business_id:
        raise HTTPException(400, "business_id query param is required")

    body = await request.body()
    row = integrations.get_connection(business_id, provider, scrub=False)
    if not row:
        raise HTTPException(404, f"{provider} is not connected for this business")

    secret = (row.get("config") or {}).get("webhook_secret", "")
    # Best-effort signature header probe — providers use different headers.
    sig = (request.headers.get("x-hub-signature-256") or
           request.headers.get("x-signature") or
           request.headers.get("x-nexus-signature") or "")
    if sig.startswith("sha256="):
        sig = sig[len("sha256="):]

    if secret and sig and not integrations.verify_webhook_signature(secret, body, sig):
        integrations.record_health(business_id, provider, ok=False,
                                   error="Webhook signature verification failed")
        raise HTTPException(401, "Signature verification failed")

    # Log as a notification so the user sees what arrived.
    try:
        preview = body.decode("utf-8", errors="replace")[:500]
        try:
            parsed = _json.loads(body)
            preview = _json.dumps(parsed)[:500]
        except Exception:
            pass
        notifications.push(
            title=f"{row['provider_meta'].get('name', provider)} webhook",
            message=preview,
            type=f"webhook_{provider}",
            severity="info",
            business_id=business_id,
        )
    except Exception as e:
        logger.warning(f"[webhook:{provider}] notify failed: {e}")

    integrations.record_health(business_id, provider, ok=True, error="")
    return {"ok": True}
