"""
Onboarding wizard endpoints — 6-step first-run flow tracked server-side so
it resumes across logins / devices.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_context

router = APIRouter(tags=["onboarding"])


class ProfileExtras(BaseModel):
    business_type: str = ""
    company_size:  str = ""
    primary_goal:  str = ""


@router.get("/api/onboarding")
def onboarding_state(ctx: dict = Depends(get_current_context)):
    """Current onboarding progress for the logged-in user in the active business."""
    from api import onboarding
    return onboarding.get_state(ctx["business_id"], ctx["user"]["id"])


@router.post("/api/onboarding/complete/{step_key}")
def onboarding_complete(step_key: str, ctx: dict = Depends(get_current_context)):
    """Mark an onboarding step as done."""
    from api import onboarding
    try:
        return onboarding.complete_step(ctx["business_id"], ctx["user"]["id"], step_key)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/api/onboarding/industry-preset")
def onboarding_industry_preset(ctx: dict = Depends(get_current_context)):
    """Preview the preset for the active business industry."""
    from api.businesses import get_business
    from api.industry_setup import get_preset

    biz = get_business(ctx["business_id"]) or {}
    return get_preset(biz.get("industry") or "")


@router.post("/api/onboarding/industry-setup")
def onboarding_industry_setup(ctx: dict = Depends(get_current_context)):
    """Apply industry-aware workspace defaults and mark the agents step done."""
    from api import onboarding
    from api.businesses import get_business
    from api.industry_setup import apply_industry_setup

    biz = get_business(ctx["business_id"]) or {}
    result = apply_industry_setup(
        ctx["business_id"],
        ctx["user"]["id"],
        biz.get("industry") or "",
    )
    try:
        state = onboarding.complete_step(ctx["business_id"], ctx["user"]["id"], "agents")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"setup": result, "onboarding": state}


@router.post("/api/onboarding/skip")
def onboarding_skip(ctx: dict = Depends(get_current_context)):
    """Dismiss the whole wizard. Checklist widget hides until /reopen is called."""
    from api import onboarding
    return onboarding.skip_all(ctx["business_id"], ctx["user"]["id"])


@router.post("/api/onboarding/reopen")
def onboarding_reopen(ctx: dict = Depends(get_current_context)):
    """Bring the wizard back — useful if the user accidentally clicked Skip."""
    from api import onboarding
    return onboarding.reopen(ctx["business_id"], ctx["user"]["id"])


@router.post("/api/onboarding/profile-extras")
def onboarding_profile_extras(req: ProfileExtras, ctx: dict = Depends(get_current_context)):
    """Persist business_type / company_size / primary_goal into the active
    business's settings.profile. Called by the wizard alongside the existing
    update_business call so these structured fields become first-class
    workspace metadata instead of free-text inside the description."""
    from api import onboarding
    profile = onboarding.set_profile_extras(
        ctx["business_id"],
        business_type=req.business_type,
        company_size=req.company_size,
        primary_goal=req.primary_goal,
    )
    return {"profile": profile}


@router.get("/api/onboarding/profile-extras")
def onboarding_get_profile_extras(ctx: dict = Depends(get_current_context)):
    """Read what's already saved — used by the wizard to pre-fill form
    fields on re-entry and by the dashboard to tune KPI selection."""
    from api import onboarding
    return {"profile": onboarding.get_profile_extras(ctx["business_id"])}


# ── Greetings ────────────────────────────────────────────────────────────
# WhatsApp bridge + Vox voice agent fetch these to construct the first
# message/call line. Stored on settings.greetings — when industry is
# applied we seed default copy; the workspace can override later.
@router.get("/api/business/greetings")
def get_business_greetings(ctx: dict = Depends(get_current_context)):
    """Return the active workspace's WhatsApp auto-reply + Vox voice opener.

    Resolution order:
      1. business.settings.greetings (customised or industry-seeded)
      2. GREETINGS for the business's industry
      3. DEFAULT_GREETINGS (industry unknown)
    """
    import json as _json
    from api.businesses import BUSINESSES_TABLE
    from api.industry_setup import get_greetings as _get_greetings
    from config.db import get_conn

    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT industry, settings FROM {BUSINESSES_TABLE} WHERE id = ?",
            (ctx["business_id"],),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Business not found")

    industry = row[0] or ""
    try:
        settings = _json.loads(row[1] or "{}")
    except Exception:
        settings = {}
    stored = settings.get("greetings") or {}
    fallback = _get_greetings(industry)
    return {
        "whatsapp":      stored.get("whatsapp")      or fallback["whatsapp"],
        "voice_opener":  stored.get("voice_opener")  or fallback["voice_opener"],
        "industry":      industry,
        "_source":       stored.get("_source") or "fallback",
    }


# ── Dashboard industry-aware KPIs ────────────────────────────────────────
# Single endpoint that returns the 4 KPI tiles tuned for the workspace's
# industry. Computed in-process from already-fetched CRM data — no extra
# DB round-trips beyond the dashboard's normal tier-2 fetches.
@router.get("/api/dashboard/industry-kpis")
def dashboard_industry_kpis(ctx: dict = Depends(get_current_context)):
    """Return 4 industry-aware KPI tiles for the dashboard.

    Each tile: {label, value, sub, tone}. Frontend renders directly.
    """
    from api.industry_kpis import compute_kpis
    from api.businesses import get_business
    from api import crm as _crm
    from api import tasks as _tasks
    from api import invoices as _inv

    biz = get_business(ctx["business_id"]) or {}
    industry = biz.get("industry") or ""

    # Pull the same data the dashboard's tier-2 calls already use.
    # Each is wrapped so a single failed dependency doesn't drop the KPIs.
    try:
        pipe = _crm.deal_pipeline_stats(ctx["business_id"]) or {}
    except Exception:
        pipe = {}
    try:
        crm_overview = _crm.crm_overview(ctx["business_id"]) or {}
    except Exception:
        crm_overview = {}
    try:
        tasks_summary = _tasks.task_summary(ctx["business_id"]) or {}
    except Exception:
        tasks_summary = {}
    try:
        inv_summary = _inv.invoice_summary(ctx["business_id"]) or {}
    except Exception:
        inv_summary = {}

    tiles = compute_kpis(
        industry=industry,
        pipe=pipe,
        tasks=tasks_summary,
        invoices=inv_summary,
        crm=crm_overview,
    )
    return {"industry": industry, "tiles": tiles}


class GreetingsUpdate(BaseModel):
    whatsapp:     str | None = None
    voice_opener: str | None = None


@router.put("/api/business/greetings")
def update_business_greetings(req: GreetingsUpdate, ctx: dict = Depends(get_current_context)):
    """Customise the workspace's WhatsApp + voice opener copy. Marks the
    record `_customised` so re-applying the industry preset doesn't
    overwrite intentional tone tuning."""
    import json as _json
    from api.businesses import BUSINESSES_TABLE
    from config.db import get_conn
    from utils.timez import now_iso as _now_iso

    if not (req.whatsapp or req.voice_opener):
        raise HTTPException(400, "Provide at least one field to update")

    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT settings FROM {BUSINESSES_TABLE} WHERE id = ?",
            (ctx["business_id"],),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Business not found")
        try:
            settings = _json.loads(row[0] or "{}")
        except Exception:
            settings = {}
        g = settings.get("greetings") or {}
        if req.whatsapp is not None:     g["whatsapp"] = req.whatsapp.strip()
        if req.voice_opener is not None: g["voice_opener"] = req.voice_opener.strip()
        g["_customised"] = True
        g["_source"] = "user_customised"
        settings["greetings"] = g
        conn.execute(
            f"UPDATE {BUSINESSES_TABLE} SET settings = ?, updated_at = ? WHERE id = ?",
            (_json.dumps(settings), _now_iso(), ctx["business_id"]),
        )
        conn.commit()
        return {"greetings": g}
    finally:
        conn.close()
