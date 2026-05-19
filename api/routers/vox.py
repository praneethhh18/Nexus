"""
Vox call audit + usage endpoints.

The frontend (VoxAgent.jsx) calls these routes to show:
  - Pending approval queue (filtered from /api/approvals)
  - Recent calls with transcripts + summaries
  - Today's usage (minutes, cap, cost estimate)
  - Manual dial endpoint

All data comes from existing systems:
  - voice_calls.py stores call records
  - approvals queue for pending dials
  - Usage metrics for cost tracking
"""
from __future__ import annotations

import hashlib
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import get_current_context
from api import voice_calls as _voice_calls

router = APIRouter(tags=["vox"])


# ── Recent calls (for Vox agent audit log) ────────────────────────────────
@router.get("/api/vox/calls")
def list_vox_calls(
    limit: int = Query(50, ge=1, le=500),
    ctx: dict = Depends(get_current_context),
):
    """List recent Vox calls for the current business.
    
    Returns wrapped records with field aliases for frontend compatibility:
      - id → call_id
      - call_sid → call_sid (unchanged)
      - transcript_sha256 (computed)
    """
    business_id = ctx["business_id"]
    calls = _voice_calls.list_for_business(business_id, limit=limit)
    
    # Wrap for frontend field expectations
    wrapped = []
    for call in calls:
        wrapped_call = dict(call)
        wrapped_call["call_id"] = call["id"]  # alias: id → call_id
        wrapped.append(wrapped_call)
    
    return {"calls": wrapped}


@router.get("/api/vox/calls/{call_id_or_sid}")
def get_vox_call(
    call_id_or_sid: str,
    ctx: dict = Depends(get_current_context),
):
    """Get one Vox call's full record (transcript + summary).
    
    Accepts either internal call_id (vc-...) or Twilio call_sid.
    """
    business_id = ctx["business_id"]
    rec = _voice_calls.get_call(business_id, call_id_or_sid)
    
    if not rec:
        raise HTTPException(404, f"call not found: {call_id_or_sid}")
    
    # Wrap for frontend field expectations
    rec["call_id"] = rec["id"]  # alias
    # Frontend reads summary.next_action, while lab stores summary.next_step.
    summary = rec.get("summary") or {}
    if summary.get("next_step") and not summary.get("next_action"):
        summary["next_action"] = summary["next_step"]
    rec["summary"] = summary
    
    # Compute transcript SHA-256 from normalized turns payload.
    turns_blob = json.dumps(rec.get("turns") or [], ensure_ascii=False, sort_keys=True)
    rec["transcript_sha256"] = hashlib.sha256(turns_blob.encode("utf-8")).hexdigest()
    
    return rec


# ── Today's usage (minutes, cap, cost) ────────────────────────────────────
@router.get("/api/vox/usage")
def get_vox_usage(ctx: dict = Depends(get_current_context)):
    """Today's voice-call usage: minutes used, daily cap, estimated cost.
    
    Returns:
      {
        "day_iso": "2026-05-17",
        "minutes_used": 23.5,
        "cap_minutes": 200,
        "calls": 5,
        "est_cost_usd": 4.70,
      }
    """
    business_id = ctx["business_id"]
    
    # Get today's calls
    calls = _voice_calls.list_for_business(business_id, limit=1000)
    
    # Filter to today
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    today_calls = [
        c for c in calls
        if c.get("started_at", "").startswith(today)
    ]
    
    # Sum duration
    total_mins = sum(c.get("duration_sec", 0) or 0 for c in today_calls) / 60.0
    
    # Get daily cap from env (default 200 minutes).
    # Support both names to stay compatible with existing .env files.
    cap_raw = (
        os.getenv("VOX_DAILY_MINUTE_CAP")
        or os.getenv("VOX_DAILY_CAP_MINUTES")
        or "200"
    )
    cap_mins = int(cap_raw)
    
    # Estimate cost: ~$0.20/min (Deepgram + TTS + LLM + Twilio SIP = ~$0.20/min)
    est_cost = total_mins * 0.20
    
    return {
        "day_iso": today,
        "minutes_used": round(total_mins, 1),
        "cap_minutes": cap_mins,
        "calls": len(today_calls),
        "calls_count": len(today_calls),
        "est_cost_usd": round(est_cost, 2),
    }


# ── Dial endpoint (approval-queued) ───────────────────────────────────────
@router.post("/api/vox/dial")
def vox_dial_contact(
    body: dict,
    ctx: dict = Depends(get_current_context),
):
    """Queue a contact dial in /api/approvals for operator approval.
    
    Body:
      {
        "contact_id": "ct-...",
        "purpose": "checking interest in demo"  (optional)
      }
    """
    business_id = ctx["business_id"]
    user_id = ctx["user"]["id"]
    contact_id = (body.get("contact_id") or "").strip()
    purpose = (body.get("purpose") or "a quick check-in").strip()
    
    if not contact_id:
        raise HTTPException(400, "contact_id is required")
    
    # Plan gate: voice starts at Pro tier
    from api.plan_gate import require_plan
    try:
        require_plan(business_id, "pro")
    except HTTPException as e:
        # Re-raise the plan gate error (402) directly to user
        raise e
    
    # Queue for approval.
    from agents import approval_queue
    action = approval_queue.queue_action(
        business_id=business_id,
        tool_name="vox_dial",
        summary=f"Dial {contact_id}",
        args={
            "contact_id": contact_id,
            "purpose": purpose,
        },
        user_id=user_id,
    )
    return {
        "ok": True,
        "queued": True,
        "action_id": action.get("id"),
        "message": f"Dial queued for approval: {contact_id}",
    }
