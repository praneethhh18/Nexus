"""Privacy Bridge router — REST surface for the SaaS bridge feature.

Endpoints:
    GET  /api/privacy-bridge          state for current business (auth)
    POST /api/privacy-bridge/token    issue a fresh registration token (auth, owner only)
    POST /api/privacy-bridge/register PUBLIC — bridge installer posts its tunnel URL + token
    POST /api/privacy-bridge/revoke   turn off the bridge (auth, owner only)
    POST /api/privacy-bridge/ping     re-check health now (auth)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api import privacy_bridge as _pb
from api.auth import get_current_context

router = APIRouter(tags=["privacy_bridge"])


@router.get("/api/privacy-bridge")
def state(ctx: dict = Depends(get_current_context)):
    return _pb.get_state(ctx["business_id"])


@router.post("/api/privacy-bridge/token")
def issue_token(ctx: dict = Depends(get_current_context)):
    """Issue a fresh registration token. Owner/admin only — bridge token
    grants the holder permission to route this business's sensitive prompts
    through their Ollama, so it has to be tightly scoped."""
    if ctx.get("business_role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can issue a Privacy Bridge token")
    token = _pb.issue_token(ctx["business_id"], ctx["user"]["id"])
    return {
        "ok":         True,
        "token":      token,
        "next_step":  (
            "Run the Privacy Bridge installer on the laptop you want to "
            "host Ollama on, paste this token when prompted. The bridge "
            "will register itself + your tunnel URL."
        ),
    }


@router.post("/api/privacy-bridge/register")
async def register(request: Request):
    """Public endpoint — the Privacy Bridge installer hits this with the
    token + its tunnel URL. No session required (bridge runs on the
    customer's laptop, not in their browser)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "body must be JSON")

    token = (body.get("token") or "").strip()
    endpoint_url = (body.get("endpoint_url") or "").strip()
    ollama_version = (body.get("ollama_version") or "").strip()
    ollama_models = body.get("ollama_models") or []

    try:
        return _pb.register_endpoint(
            token=token,
            endpoint_url=endpoint_url,
            ollama_version=ollama_version,
            ollama_models=ollama_models,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/api/privacy-bridge/revoke")
def revoke(ctx: dict = Depends(get_current_context)):
    """Turn the bridge off. Sensitive prompts will fall back to cloud
    (with PII redaction). Doesn't delete the row — call /token to fully
    rotate + start over."""
    if ctx.get("business_role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can revoke the Privacy Bridge")
    return _pb.revoke(ctx["business_id"])


@router.post("/api/privacy-bridge/ping")
def ping(ctx: dict = Depends(get_current_context)):
    """Force an immediate health check (instead of waiting for the
    background loop). Useful right after the user runs the installer."""
    return _pb.health_check_one(ctx["business_id"])
