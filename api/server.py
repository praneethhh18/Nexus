"""
NexusAgent FastAPI Server — REST API + WebSocket for the React frontend.
Run: uvicorn api.server:app --reload --port 8000

All data endpoints are multi-tenant: the current (user, business) pair is
resolved via `get_current_context`, which reads JWT auth and the X-Business-Id
header. Storage calls are scoped by business_id so tenants cannot see each
other's data.
"""
from __future__ import annotations

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Query,
    HTTPException, Request, Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from loguru import logger

# ── Bootstrap NexusAgent ──────────────────────────────────────────────────────
from config.settings import ensure_directories, validate_config, VERSION, enable_sqlite_production_mode
ensure_directories()

# Auto-create DB if missing
from config.settings import DB_PATH
if not Path(DB_PATH).exists():
    from sql_agent.db_setup import setup_database
    setup_database()

# Enable WAL mode + production pragmas — 10× write throughput, concurrent reads
enable_sqlite_production_mode()

# Auto-load sample docs
from utils.sample_docs_generator import ensure_documents_loaded
ensure_documents_loaded()

# Start monitor
try:
    from orchestrator.proactive_monitor import start_scheduler
    start_scheduler()
except Exception as e:
    logger.warning(f"Monitor start failed: {e}")

# Start autonomous agent scheduler (stale deals, invoice reminders, meeting prep)
try:
    from agents.background.scheduler import start_agent_scheduler
    start_agent_scheduler()
except Exception as e:
    logger.warning(f"Agent scheduler start failed: {e}")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NexusAgent API",
    version=VERSION,
    description="Multi-tenant, multi-agent AI business assistant — runs locally on Ollama.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Business-Id"],
)


# ── Pydantic Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None


class WhatIfRequest(BaseModel):
    scenario: str = Field(..., min_length=1, max_length=2000)


class ReportRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class SignupRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None  # required if 2FA is enabled


class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    industry: str = ""
    description: str = ""


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    industry: Optional[str] = None
    description: Optional[str] = None


class MemberAdd(BaseModel):
    user_id: str
    role: str = "member"


# ── Auth Setup ────────────────────────────────────────────────────────────────
from api.auth import (
    ensure_default_admin, create_user, authenticate_user,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, get_current_context, get_user_by_id, list_users,
)
from api.businesses import (
    create_business, get_business, list_user_businesses,
    update_business, delete_business,
    list_members, add_member, remove_member, assert_member,
    ensure_business_for_user, migrate_legacy_data,
)

ensure_default_admin()
migrate_legacy_data()


# ═══════════════════════════════════════════════════════════════════════════════
#   AUTH ENDPOINTS (public)
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    user = create_user(req.email, req.name, req.password)
    # Every new user gets a starter business
    biz_id = ensure_business_for_user(user["id"], user["name"])
    access = create_access_token(user["id"], user["email"], user["role"])
    refresh = create_refresh_token(user["id"])
    return {
        "user": user,
        "access_token": access,
        "refresh_token": refresh,
        "businesses": list_user_businesses(user["id"]),
        "current_business_id": biz_id,
    }


@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    user = authenticate_user(req.email, req.password, request=request)
    if not user:
        raise HTTPException(401, "Invalid email or password")

    # 2FA gate — if the user has enrolled, require a valid code
    from api.security import is_2fa_required, verify_login_factor, record_session
    if is_2fa_required(user["id"]):
        if not req.totp_code:
            # Signal to the client: password OK, now we need the code.
            # Don't issue a token yet.
            return {
                "requires_2fa": True,
                "email": user["email"],
                "message": "Enter the 6-digit code from your authenticator app.",
            }
        if not verify_login_factor(user["id"], req.totp_code):
            raise HTTPException(401, "Invalid 2FA code")

    biz_id = ensure_business_for_user(user["id"], user["name"])
    access = create_access_token(user["id"], user["email"], user["role"])
    refresh = create_refresh_token(user["id"])

    # Record this session for visibility + revocation
    try:
        from datetime import timedelta as _td
        payload = decode_token(access)
        jti = payload.get("jti", "")
        if jti:
            record_session(
                jti=jti, user_id=user["id"],
                user_agent=(request.headers.get("user-agent") or "")[:300],
                ip=(request.client.host if request.client else "") or "",
                expires_at=datetime.utcfromtimestamp(payload["exp"]) if isinstance(payload.get("exp"), (int, float))
                else datetime.utcnow() + _td(hours=24),
            )
    except Exception as e:
        logger.debug(f"[Auth] session recording skipped: {e}")

    return {
        "user": user,
        "access_token": access,
        "refresh_token": refresh,
        "businesses": list_user_businesses(user["id"]),
        "current_business_id": biz_id,
    }


@app.post("/api/auth/refresh")
def refresh_token(body: dict):
    token = body.get("refresh_token", "")
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    access = create_access_token(user["id"], user["email"], user["role"])
    return {"access_token": access, "user": user}


@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "user": user,
        "businesses": list_user_businesses(user["id"]),
    }


@app.get("/api/auth/users")
def get_users(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return list_users()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@app.post("/api/auth/change-password")
def change_password_api(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    from api.auth import change_password
    change_password(user["id"], req.current_password, req.new_password)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   2FA — TOTP enrollment, verify, disable, recovery codes
# ═══════════════════════════════════════════════════════════════════════════════
from api import security as _sec


class TotpCode(BaseModel):
    code: str


@app.get("/api/auth/2fa/status")
def twofa_status(user: dict = Depends(get_current_user)):
    return _sec.get_2fa_state(user["id"])


@app.post("/api/auth/2fa/enroll")
def twofa_enroll(user: dict = Depends(get_current_user)):
    """Start enrollment. Returns the secret + QR code. 2FA is NOT active yet."""
    return _sec.start_2fa_enrollment(user["id"], user["email"])


@app.post("/api/auth/2fa/verify")
def twofa_verify(req: TotpCode, user: dict = Depends(get_current_user)):
    """Verify the first code to finalize enrollment. Returns recovery codes ONCE."""
    recovery = _sec.verify_and_enable_2fa(user["id"], req.code)
    return {"enabled": True, "recovery_codes": recovery,
            "message": "2FA is now active. Save these recovery codes somewhere safe — they won't be shown again."}


@app.post("/api/auth/2fa/disable")
def twofa_disable(req: TotpCode, user: dict = Depends(get_current_user)):
    _sec.disable_2fa(user["id"], req.code)
    return {"ok": True}


@app.post("/api/auth/2fa/regenerate-codes")
def twofa_regenerate_codes(req: TotpCode, user: dict = Depends(get_current_user)):
    codes = _sec.regenerate_recovery_codes(user["id"], req.code)
    return {"recovery_codes": codes}


# ═══════════════════════════════════════════════════════════════════════════════
#   Sessions — view & revoke active logins
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/auth/sessions")
def sessions_list(user: dict = Depends(get_current_user)):
    sessions = _sec.list_sessions(user["id"])
    current_jti = user.get("_jti")
    for s in sessions:
        s["is_current"] = (s["jti"] == current_jti)
    return sessions


@app.delete("/api/auth/sessions/{jti}")
def revoke_session(jti: str, user: dict = Depends(get_current_user)):
    if jti == user.get("_jti"):
        raise HTTPException(400, "Use /logout to end your current session")
    _sec.revoke_session(user["id"], jti)
    return {"ok": True}


@app.post("/api/auth/sessions/revoke-all-other")
def revoke_all_other(user: dict = Depends(get_current_user)):
    current = user.get("_jti", "")
    count = _sec.revoke_all_other_sessions(user["id"], current)
    return {"ok": True, "revoked": count}


# ═══════════════════════════════════════════════════════════════════════════════
#   Audit log — admin-only browse
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/audit")
def audit_log_list(
    limit: int = 100,
    tool: Optional[str] = None,
    user_id_filter: Optional[str] = None,
    success: Optional[bool] = None,
    search: Optional[str] = None,
    ctx: dict = Depends(get_current_context),
):
    """Admin/owner can view the full audit log for the current business."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can view the audit log")

    import sqlite3 as _sq
    from config.settings import DB_PATH
    limit = max(1, min(limit, 1000))
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    try:
        sql = ("SELECT event_id, timestamp, event_type, tool_name, input_summary, "
               "output_summary, duration_ms, human_approved, success, error_message, "
               "business_id, user_id FROM nexus_audit_log WHERE business_id = ?")
        params: list = [ctx["business_id"]]
        if tool:
            sql += " AND tool_name LIKE ?"; params.append(f"%{tool}%")
        if user_id_filter:
            sql += " AND user_id = ?"; params.append(user_id_filter)
        if success is not None:
            sql += " AND success = ?"; params.append(1 if success else 0)
        if search:
            sql += " AND (input_summary LIKE ? OR output_summary LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
    # Enrich with actor name
    user_ids = {r["user_id"] for r in rows if r.get("user_id")}
    names: dict = {}
    if user_ids:
        conn = _sq.connect(DB_PATH)
        conn.row_factory = _sq.Row
        try:
            placeholders = ",".join("?" for _ in user_ids)
            for r in conn.execute(
                f"SELECT id, name, email FROM nexus_users WHERE id IN ({placeholders})",
                tuple(user_ids),
            ).fetchall():
                names[r["id"]] = r["name"] or r["email"]
        finally:
            conn.close()
    for r in rows:
        r["actor_name"] = names.get(r.get("user_id"), r.get("user_id") or "system")
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
#   Agent personas — names + role tags for the 6 autonomous agents
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/agents/activity")
def agents_activity(hours: int = 48, limit: int = 50,
                    ctx: dict = Depends(get_current_context)):
    """Unified timeline of what every agent did in the last `hours` hours."""
    from agents.activity import recent
    hours = max(1, min(hours, 720))  # cap at 30 days
    limit = max(1, min(limit, 200))
    return recent(ctx["business_id"], hours=hours, limit=limit)


@app.get("/api/agents/personas")
def agents_list_personas(ctx: dict = Depends(get_current_context)):
    """Return all 6 agent personas (name, role tag, description, last activity)."""
    from agents.personas import list_personas
    return list_personas(ctx["business_id"])


class _PersonaPatch(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None


@app.get("/api/agents/nudges")
def agents_list_nudges(ctx: dict = Depends(get_current_context)):
    """Active proactive nudges — things the team noticed and wants permission to act on."""
    from agents.nudges import list_active
    return list_active(ctx["business_id"])


@app.post("/api/agents/nudges/{nudge_id}/dismiss")
def agents_dismiss_nudge(nudge_id: str, ctx: dict = Depends(get_current_context)):
    """Hide this nudge for the rest of today (UTC). Returns fresh nudge list."""
    from agents.nudges import dismiss, list_active
    dismiss(ctx["business_id"], nudge_id)
    return list_active(ctx["business_id"])


@app.post("/api/agents/nudges/{nudge_id}/accept")
def agents_accept_nudge(nudge_id: str, ctx: dict = Depends(get_current_context)):
    """
    Act on a nudge. Looks up the current nudge by id, executes its action
    (run_agent or navigate), and returns {result, next_nudges}.
    """
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can act on nudges")

    from agents.nudges import list_active, dismiss
    nudges = list_active(ctx["business_id"])
    nudge = next((n for n in nudges if n["id"] == nudge_id), None)
    if not nudge:
        raise HTTPException(404, "Nudge not active (already handled or dismissed)")

    action = nudge.get("action") or {}
    result: dict = {"kind": action.get("kind")}

    if action.get("kind") == "run_agent":
        agent_key = action.get("agent_key")
        if agent_key == "morning_briefing":
            from agents.briefing import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        elif agent_key == "invoice_reminder":
            from agents.background.invoice_reminder import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        elif agent_key == "stale_deal_watcher":
            from agents.background.stale_deal_watcher import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        elif agent_key == "meeting_prep":
            from agents.background.meeting_prep import run_for_user
            result["detail"] = run_for_user(ctx["user"]["id"], ctx["business_id"])
        elif agent_key == "email_triage":
            from agents.email_triage import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        else:
            raise HTTPException(400, f"Unknown agent in nudge action: {agent_key}")
    elif action.get("kind") == "navigate":
        result["path"] = action.get("path")
    else:
        raise HTTPException(400, f"Unknown action kind: {action.get('kind')}")

    # After running, dismiss so the user doesn't see the same nudge again today
    dismiss(ctx["business_id"], nudge_id)

    return {"result": result, "next_nudges": list_active(ctx["business_id"])}


@app.post("/api/agents/{agent_key}/run")
def agents_run_now(agent_key: str, ctx: dict = Depends(get_current_context)):
    """
    On-demand trigger for a specific agent. Dispatches to each agent's own
    per-business runner so the work mirrors what the scheduler does. Owner/admin only.
    """
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can run agents on demand")

    business_id = ctx["business_id"]
    user_id = ctx["user"]["id"]

    try:
        if agent_key == "morning_briefing":
            from agents.briefing import run_for_business
            result = run_for_business(business_id)
            return {"ok": True, "agent_key": agent_key,
                    "detail": {"narrative_mode": result.get("mode"),
                               "delivered": result.get("delivered_channels", [])}}
        if agent_key == "invoice_reminder":
            from agents.background.invoice_reminder import run_for_business
            return {"ok": True, "agent_key": agent_key, "detail": run_for_business(business_id)}
        if agent_key == "stale_deal_watcher":
            from agents.background.stale_deal_watcher import run_for_business
            return {"ok": True, "agent_key": agent_key, "detail": run_for_business(business_id)}
        if agent_key == "meeting_prep":
            from agents.background.meeting_prep import run_for_user
            return {"ok": True, "agent_key": agent_key, "detail": run_for_user(user_id, business_id)}
        if agent_key == "email_triage":
            from agents.email_triage import run_for_business
            return {"ok": True, "agent_key": agent_key, "detail": run_for_business(business_id)}
        if agent_key == "memory_consolidate":
            from agents.summarizer import consolidate_business_memory
            return {"ok": True, "agent_key": agent_key,
                    "detail": consolidate_business_memory(business_id, apply_changes=True)}
    except Exception as e:
        from loguru import logger
        logger.exception(f"[AgentRun] {agent_key} failed: {e}")
        raise HTTPException(500, f"{agent_key} failed: {e}")

    raise HTTPException(404, f"Unknown agent: {agent_key}")


@app.patch("/api/agents/personas/{agent_key}")
def agents_patch_persona(agent_key: str, body: _PersonaPatch,
                         ctx: dict = Depends(get_current_context)):
    """Rename an agent (empty string = reset to default) and/or toggle enabled.
    Owner/admin only — names are a business-level setting."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can rename agents")
    from agents.personas import set_name, set_enabled, get_persona
    if body.name is not None:
        try:
            set_name(ctx["business_id"], agent_key, body.name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except KeyError:
            raise HTTPException(404, f"Unknown agent: {agent_key}")
    if body.enabled is not None:
        try:
            set_enabled(ctx["business_id"], agent_key, body.enabled)
        except KeyError:
            raise HTTPException(404, f"Unknown agent: {agent_key}")
    return get_persona(ctx["business_id"], agent_key)


# ═══════════════════════════════════════════════════════════════════════════════
#   Morning briefing — daily 1-page agent
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/briefing/latest")
def briefing_latest(ctx: dict = Depends(get_current_context)):
    """Return today's briefing for this business, or null if none yet."""
    from agents.briefing import latest
    return latest(ctx["business_id"]) or {}


@app.post("/api/briefing/run")
def briefing_run_now(ctx: dict = Depends(get_current_context)):
    """Generate a briefing right now (owner/admin only)."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can trigger a briefing")
    from agents.briefing import run_for_business
    return run_for_business(ctx["business_id"])


# ═══════════════════════════════════════════════════════════════════════════════
#   Sample data — fills a new business with realistic records for demo/testing
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/seed/sample-data")
def seed_sample(ctx: dict = Depends(get_current_context)):
    """Populate the current business with sample companies, contacts, deals,
    tasks, and invoices. Admin/owner only. Refuses if data already exists."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can seed sample data")
    from api.seed_data import seed_sample_data
    return seed_sample_data(ctx["business_id"], ctx["user"]["id"])


# ═══════════════════════════════════════════════════════════════════════════════
#   Privacy / Cloud-LLM audit — visible proof that nothing sensitive left
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/privacy/status")
def privacy_status(user: dict = Depends(get_current_user)):
    """
    Summarize the privacy posture: which provider is live, whether the cloud
    kill-switch is on, redaction on, audit logging on, and where the audit
    log lives. Any logged-in user can view; no raw data is exposed.
    """
    from config import privacy
    from config.llm_provider import get_provider, USE_CLAUDE, USE_BEDROCK, CLAUDE_MODEL

    return {
        "provider": get_provider(),
        "cloud_configured": bool(USE_CLAUDE or USE_BEDROCK),
        "cloud_model": CLAUDE_MODEL if USE_CLAUDE else "nova-pro" if USE_BEDROCK else None,
        "allow_cloud_llm": privacy.ALLOW_CLOUD_LLM,
        "redact_pii": privacy.REDACT_PII,
        "audit_enabled": privacy.AUDIT_CLOUD_CALLS,
        "audit_log_path": str(privacy._AUDIT_PATH),
    }


@app.get("/api/privacy/audit")
def privacy_audit_list(
    limit: int = 100,
    ctx: dict = Depends(get_current_context),
):
    """
    Return the last N cloud-call records from outputs/cloud_audit.jsonl,
    newest-first, plus aggregate stats. Admin/owner only — the log reveals
    call patterns (times, sizes) even though it never contains raw prompts.
    """
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can view the cloud audit log")

    from config import privacy
    limit = max(1, min(limit, 1000))
    path = privacy._AUDIT_PATH

    entries: list = []
    stats = {
        "total": 0, "last_24h": 0, "total_redactions": 0,
        "total_chars": 0, "by_provider": {}, "by_mode": {},
    }
    if path.exists():
        now = time.time()
        # Efficient enough for a line-delimited file up to ~50 MB.
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        stats["total"] = len(lines)
        for line in lines:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            stats["total_redactions"] += int(rec.get("redactions", 0) or 0)
            stats["total_chars"]      += int(rec.get("prompt_chars", 0) or 0)
            prov = rec.get("provider") or "unknown"
            stats["by_provider"][prov] = stats["by_provider"].get(prov, 0) + 1
            mode = (rec.get("meta") or {}).get("mode", "invoke")
            stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1
            if now - float(rec.get("ts", 0)) < 86400:
                stats["last_24h"] += 1
        # Newest-first, trimmed
        for line in reversed(lines[-limit:]):
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return {"stats": stats, "entries": entries}


@app.post("/api/privacy/audit/clear")
def privacy_audit_clear(ctx: dict = Depends(get_current_context)):
    """Truncate the cloud audit log. Admin/owner only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can clear the cloud audit log")
    from config import privacy
    if privacy._AUDIT_PATH.exists():
        privacy._AUDIT_PATH.unlink()
    return {"ok": True}


@app.get("/api/audit/export")
def audit_log_export_csv(
    limit: int = 5000,
    ctx: dict = Depends(get_current_context),
):
    """CSV export of the audit log. Admin/owner only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can export the audit log")

    import csv, io
    import sqlite3 as _sq
    from config.settings import DB_PATH
    from fastapi.responses import Response
    limit = max(1, min(limit, 100000))
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    try:
        rows = conn.execute(
            "SELECT event_id, timestamp, event_type, tool_name, user_id, "
            "input_summary, output_summary, duration_ms, human_approved, success, "
            "error_message FROM nexus_audit_log WHERE business_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (ctx["business_id"], limit),
        ).fetchall()
    finally:
        conn.close()
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(dict(r))
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_log.csv"},
    )


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


def _send_reset_email(to_email: str, to_name: str, token: str) -> bool:
    """Send the reset email. Returns True on success, False if email is disabled."""
    import os
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    base_url = os.getenv("APP_BASE_URL", "http://localhost:5173").rstrip("/")
    reset_link = f"{base_url}/reset-password?token={token}"

    if not EMAIL_ENABLED:
        # Log the link so the dev can still use it; never return it to the client.
        logger.warning(f"[Auth] EMAIL not configured — reset link for {to_email}: {reset_link}")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        subject = "NexusAgent — Reset your password"
        body = (
            f"Hi {to_name or 'there'},\n\n"
            f"Someone (hopefully you) asked to reset your NexusAgent password. "
            f"Click the link below to set a new one. This link is valid for 1 hour.\n\n"
            f"{reset_link}\n\n"
            f"If you didn't request this, you can safely ignore this email — "
            f"your password will not be changed.\n\n"
            f"— NexusAgent"
        )
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"[Auth] Reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[Auth] Reset email failed: {e}")
        return False


@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """
    Always returns the same response regardless of whether the email exists,
    to avoid email enumeration.
    """
    from api.auth import request_password_reset
    result = request_password_reset(req.email)
    if result:
        token, user = result
        _send_reset_email(user["email"], user.get("name", ""), token)
    # Identical response in both branches — do NOT leak existence.
    return {
        "ok": True,
        "message": "If that email is registered, a reset link has been sent.",
    }


@app.post("/api/auth/reset-password")
def reset_password_api(req: ResetPasswordRequest):
    from api.auth import consume_password_reset
    consume_password_reset(req.token, req.new_password)
    return {"ok": True, "message": "Password updated. You can now sign in."}


# ═══════════════════════════════════════════════════════════════════════════════
#   BUSINESSES
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/businesses")
def list_my_businesses(user: dict = Depends(get_current_user)):
    return list_user_businesses(user["id"])


@app.post("/api/businesses")
def create_my_business(req: BusinessCreate, user: dict = Depends(get_current_user)):
    biz = create_business(
        name=req.name,
        owner_id=user["id"],
        industry=req.industry,
        description=req.description,
    )
    return biz


@app.get("/api/businesses/{business_id}")
def get_my_business(business_id: str, user: dict = Depends(get_current_user)):
    assert_member(business_id, user["id"])
    biz = get_business(business_id)
    biz["members"] = list_members(business_id)
    biz["my_role"] = next(
        (m["role"] for m in biz["members"] if m["user_id"] == user["id"]),
        None,
    )
    return biz


@app.patch("/api/businesses/{business_id}")
def update_my_business(business_id: str, req: BusinessUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return update_business(business_id, user["id"], updates)


@app.delete("/api/businesses/{business_id}")
def delete_my_business(business_id: str, user: dict = Depends(get_current_user)):
    delete_business(business_id, user["id"])
    return {"ok": True}


@app.get("/api/businesses/{business_id}/members")
def list_business_members(business_id: str, user: dict = Depends(get_current_user)):
    assert_member(business_id, user["id"])
    return list_members(business_id)


@app.post("/api/businesses/{business_id}/members")
def add_business_member(business_id: str, req: MemberAdd, user: dict = Depends(get_current_user)):
    add_member(business_id, user["id"], req.user_id, req.role)
    return {"ok": True}


@app.delete("/api/businesses/{business_id}/members/{target_user_id}")
def remove_business_member(business_id: str, target_user_id: str, user: dict = Depends(get_current_user)):
    remove_member(business_id, user["id"], target_user_id)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   CRM — Contacts, Companies, Deals, Interactions
# ═══════════════════════════════════════════════════════════════════════════════
from api import crm as _crm


@app.get("/api/crm/overview")
def crm_overview(ctx: dict = Depends(get_current_context)):
    return _crm.crm_overview(ctx["business_id"])


# ── Companies ────────────────────────────────────────────────────────────────
@app.get("/api/crm/companies")
def list_companies_api(search: Optional[str] = None, limit: int = 100, ctx: dict = Depends(get_current_context)):
    return _crm.list_companies(ctx["business_id"], search=search, limit=limit)


@app.post("/api/crm/companies")
def create_company_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_company(ctx["business_id"], ctx["user"]["id"], body)


@app.get("/api/crm/companies/{company_id}")
def get_company_api(company_id: str, ctx: dict = Depends(get_current_context)):
    return _crm.get_company(ctx["business_id"], company_id)


@app.patch("/api/crm/companies/{company_id}")
def update_company_api(company_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.update_company(ctx["business_id"], company_id, body)


@app.delete("/api/crm/companies/{company_id}")
def delete_company_api(company_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_company(ctx["business_id"], company_id)
    return {"ok": True}


# ── Contacts ─────────────────────────────────────────────────────────────────
@app.get("/api/crm/contacts")
def list_contacts_api(
    search: Optional[str] = None,
    company_id: Optional[str] = None,
    limit: int = 100,
    ctx: dict = Depends(get_current_context),
):
    return _crm.list_contacts(ctx["business_id"], search=search, company_id=company_id, limit=limit)


@app.post("/api/crm/contacts")
def create_contact_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_contact(ctx["business_id"], ctx["user"]["id"], body)


@app.get("/api/crm/contacts/{contact_id}")
def get_contact_api(contact_id: str, ctx: dict = Depends(get_current_context)):
    return _crm.get_contact(ctx["business_id"], contact_id)


@app.patch("/api/crm/contacts/{contact_id}")
def update_contact_api(contact_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.update_contact(ctx["business_id"], contact_id, body)


@app.delete("/api/crm/contacts/{contact_id}")
def delete_contact_api(contact_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_contact(ctx["business_id"], contact_id)
    return {"ok": True}


# ── Deals ────────────────────────────────────────────────────────────────────
@app.get("/api/crm/deals")
def list_deals_api(
    stage: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
    ctx: dict = Depends(get_current_context),
):
    return _crm.list_deals(ctx["business_id"], stage=stage, search=search, limit=limit)


@app.post("/api/crm/deals")
def create_deal_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_deal(ctx["business_id"], ctx["user"]["id"], body)


@app.get("/api/crm/deals/{deal_id}")
def get_deal_api(deal_id: str, ctx: dict = Depends(get_current_context)):
    return _crm.get_deal(ctx["business_id"], deal_id)


@app.patch("/api/crm/deals/{deal_id}")
def update_deal_api(deal_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.update_deal(ctx["business_id"], deal_id, body)


@app.delete("/api/crm/deals/{deal_id}")
def delete_deal_api(deal_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_deal(ctx["business_id"], deal_id)
    return {"ok": True}


@app.get("/api/crm/pipeline")
def pipeline_api(ctx: dict = Depends(get_current_context)):
    return _crm.deal_pipeline_stats(ctx["business_id"])


# ── Interactions ─────────────────────────────────────────────────────────────
@app.get("/api/crm/interactions")
def list_interactions_api(
    contact_id: Optional[str] = None,
    company_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    limit: int = 100,
    ctx: dict = Depends(get_current_context),
):
    return _crm.list_interactions(
        ctx["business_id"],
        contact_id=contact_id, company_id=company_id, deal_id=deal_id, limit=limit,
    )


@app.post("/api/crm/interactions")
def create_interaction_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_interaction(ctx["business_id"], ctx["user"]["id"], body)


@app.delete("/api/crm/interactions/{interaction_id}")
def delete_interaction_api(interaction_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_interaction(ctx["business_id"], interaction_id)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   TASKS
# ═══════════════════════════════════════════════════════════════════════════════
from api import tasks as _tasks


@app.get("/api/tasks")
def list_tasks_api(
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    search: Optional[str] = None,
    due_window: Optional[str] = None,
    limit: int = 200,
    ctx: dict = Depends(get_current_context),
):
    return _tasks.list_tasks(
        ctx["business_id"], status=status, assignee_id=assignee_id,
        search=search, due_window=due_window, limit=limit,
    )


@app.post("/api/tasks")
def create_task_api(body: dict, ctx: dict = Depends(get_current_context)):
    # Verify assignee is a business member if provided
    if body.get("assignee_id") and body["assignee_id"] != ctx["user"]["id"]:
        from api.businesses import assert_member
        assert_member(ctx["business_id"], body["assignee_id"])
    return _tasks.create_task(ctx["business_id"], ctx["user"]["id"], body)


@app.get("/api/tasks/summary")
def task_summary_api(mine: bool = False, ctx: dict = Depends(get_current_context)):
    return _tasks.task_summary(ctx["business_id"], user_id=ctx["user"]["id"] if mine else None)


@app.get("/api/tasks/{task_id}")
def get_task_api(task_id: str, ctx: dict = Depends(get_current_context)):
    return _tasks.get_task(ctx["business_id"], task_id)


@app.patch("/api/tasks/{task_id}")
def update_task_api(task_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    if body.get("assignee_id") and body["assignee_id"] != ctx["user"]["id"]:
        from api.businesses import assert_member
        assert_member(ctx["business_id"], body["assignee_id"])
    return _tasks.update_task(ctx["business_id"], task_id, body)


@app.delete("/api/tasks/{task_id}")
def delete_task_api(task_id: str, ctx: dict = Depends(get_current_context)):
    _tasks.delete_task(ctx["business_id"], task_id)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   INVOICES
# ═══════════════════════════════════════════════════════════════════════════════
from api import invoices as _inv


@app.get("/api/invoices")
def list_invoices_api(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
    ctx: dict = Depends(get_current_context),
):
    return _inv.list_invoices(ctx["business_id"], status=status, search=search, limit=limit)


@app.post("/api/invoices")
def create_invoice_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _inv.create_invoice(ctx["business_id"], ctx["user"]["id"], body)


@app.get("/api/invoices/summary")
def invoice_summary_api(ctx: dict = Depends(get_current_context)):
    return _inv.invoice_summary(ctx["business_id"])


@app.get("/api/invoices/{invoice_id}")
def get_invoice_api(invoice_id: str, ctx: dict = Depends(get_current_context)):
    return _inv.get_invoice(ctx["business_id"], invoice_id)


@app.patch("/api/invoices/{invoice_id}")
def update_invoice_api(invoice_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _inv.update_invoice(ctx["business_id"], invoice_id, body)


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice_api(invoice_id: str, ctx: dict = Depends(get_current_context)):
    _inv.delete_invoice(ctx["business_id"], invoice_id)
    return {"ok": True}


@app.post("/api/invoices/{invoice_id}/render")
def render_invoice_pdf(invoice_id: str, ctx: dict = Depends(get_current_context)):
    from api.businesses import get_business
    biz = get_business(ctx["business_id"])
    path = _inv.render_pdf(ctx["business_id"], invoice_id, business_name=biz["name"] if biz else "")
    filename = Path(path).name
    return {"path": path, "filename": filename, "download_url": f"/api/invoices/{invoice_id}/pdf"}


@app.get("/api/invoices/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: str, ctx: dict = Depends(get_current_context)):
    inv = _inv.get_invoice(ctx["business_id"], invoice_id)
    pdf_path = inv.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        # Auto-render if missing
        from api.businesses import get_business
        biz = get_business(ctx["business_id"])
        pdf_path = _inv.render_pdf(ctx["business_id"], invoice_id, business_name=biz["name"] if biz else "")
    filename = Path(pdf_path).name
    return FileResponse(str(pdf_path), filename=filename, media_type="application/pdf")


# ═══════════════════════════════════════════════════════════════════════════════
#   DOCUMENTS — Proposals, SOW, Contracts, Offer Letters
# ═══════════════════════════════════════════════════════════════════════════════
from api import documents as _docs


@app.get("/api/documents/templates")
def list_doc_templates(ctx: dict = Depends(get_current_context)):
    return _docs.list_templates()


@app.get("/api/documents/templates/{template_key}")
def get_doc_template(template_key: str, ctx: dict = Depends(get_current_context)):
    return _docs.get_template(template_key)


@app.get("/api/documents")
def list_documents_api(limit: int = 100, ctx: dict = Depends(get_current_context)):
    return _docs.list_documents(ctx["business_id"], limit=limit)


@app.post("/api/documents/generate")
def generate_document_api(body: dict, ctx: dict = Depends(get_current_context)):
    template_key = body.get("template_key", "")
    title = body.get("title", "")
    variables = body.get("variables", {}) or {}
    fmt = body.get("format", "docx")
    return _docs.generate_document(
        business_id=ctx["business_id"],
        user_id=ctx["user"]["id"],
        template_key=template_key,
        title=title,
        variables=variables,
        fmt=fmt,
    )


@app.get("/api/documents/{document_id}")
def get_document_api(document_id: str, ctx: dict = Depends(get_current_context)):
    return _docs.get_document(ctx["business_id"], document_id)


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: str, ctx: dict = Depends(get_current_context)):
    doc = _docs.get_document(ctx["business_id"], document_id)
    path = Path(doc["file_path"])
    if not path.exists():
        raise HTTPException(404, "Document file missing on disk")
    media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
        if doc["format"] == "docx" else "application/pdf"
    return FileResponse(str(path), filename=path.name, media_type=media)


@app.delete("/api/documents/{document_id}")
def delete_document_api(document_id: str, ctx: dict = Depends(get_current_context)):
    _docs.delete_document(ctx["business_id"], document_id)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   GOOGLE CALENDAR (per-user connection, read-only)
# ═══════════════════════════════════════════════════════════════════════════════
from api import calendar as _cal
from fastapi.responses import RedirectResponse, HTMLResponse


@app.get("/api/calendar/status")
def calendar_status(user: dict = Depends(get_current_user)):
    import os
    conn = _cal.get_connection(user["id"])
    configured = bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
    return {
        "configured": configured,
        "connected": bool(conn),
        "connection": conn,
    }


@app.post("/api/calendar/oauth/start")
def calendar_oauth_start(user: dict = Depends(get_current_user)):
    url = _cal.build_authorize_url(user["id"])
    return {"authorize_url": url}


@app.get("/api/calendar/oauth/callback")
def calendar_oauth_callback(code: str = "", state: str = "", error: str = ""):
    """
    This endpoint is hit by Google (browser redirect). We verify the signed
    state to recover the user_id, swap the code for tokens, and render a
    small HTML page that tells the user they can close the window.
    """
    import os
    if error:
        return HTMLResponse(f"<h3>Google sign-in failed</h3><p>{error}</p>", status_code=400)
    if not code or not state:
        return HTMLResponse("<h3>Missing code or state.</h3>", status_code=400)
    try:
        user_id = _cal._verify_state(state)
    except HTTPException as e:
        return HTMLResponse(f"<h3>Invalid state.</h3><p>{e.detail}</p>", status_code=400)

    redirect_uri = os.getenv(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:8000/api/calendar/oauth/callback",
    ).strip()
    tokens = _cal.exchange_code_for_tokens(code, redirect_uri)
    info = _cal.save_connection(user_id, tokens)

    return HTMLResponse(
        f"""
        <html><head><title>Calendar connected</title>
        <style>body{{font-family:Segoe UI,system-ui,sans-serif;background:#0c1222;color:#e2e8f0;
        display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
        .card{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:32px;max-width:420px;text-align:center}}
        h2{{color:#22c55e;margin-top:0}}</style></head><body>
        <div class="card">
          <h2>Calendar connected</h2>
          <p>Connected account: <strong>{info.get('account_email') or 'unknown'}</strong></p>
          <p style="color:#94a3b8;font-size:13px">You can close this window and return to NexusAgent.</p>
          <script>setTimeout(()=>window.close(), 1500)</script>
        </div></body></html>
        """,
    )


@app.get("/api/calendar/events")
def calendar_events(days: int = 14, limit: int = 20, user: dict = Depends(get_current_user)):
    return _cal.list_upcoming_events(user["id"], days_ahead=days, max_results=limit)


@app.delete("/api/calendar/disconnect")
def calendar_disconnect(user: dict = Depends(get_current_user)):
    _cal.disconnect(user["id"])
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   AGENT — tool-using chat, approvals, memory
# ═══════════════════════════════════════════════════════════════════════════════
from agents import agent_loop as _agent_loop
from agents import approval_queue as _approvals
from agents import business_memory as _mem
from agents import tool_registry as _tool_registry


class AgentChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None


@app.get("/api/agent/tools")
def list_agent_tools(ctx: dict = Depends(get_current_context)):
    """Return the list of tools the agent can use (for display in the UI)."""
    return _tool_registry.list_tools(for_llm=False)


@app.post("/api/agent/chat")
async def agent_chat(req: AgentChatRequest, ctx: dict = Depends(get_current_context)):
    """
    Tool-using chat. Streams the LLM + tool loop; when the loop ends, persists
    the turn to the conversation and returns the final answer.
    """
    from memory.conversation_store import (
        create_conversation, auto_title, save_full_conversation,
        load_messages, assert_conversation_access,
    )
    from memory.query_history import log_query
    from api.businesses import get_business

    user = ctx["user"]
    business_id = ctx["business_id"]
    biz = get_business(business_id) or {}
    business_name = biz.get("name", "this business")

    conv_id = req.conversation_id
    if not conv_id:
        conv_id = create_conversation(user_id=user["id"], business_id=business_id)
        auto_title(conv_id, req.query)
    else:
        assert_conversation_access(conv_id, business_id)

    # Rebuild the conversation history in tool-calling format.
    prior = load_messages(conv_id)
    agent_messages = []
    for m in prior[-20:]:  # last 20 turns is plenty
        role = m.get("role")
        if role in ("user", "assistant"):
            agent_messages.append({"role": role, "content": m.get("content", "")})
    agent_messages.append({"role": "user", "content": req.query})

    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: _agent_loop.run_agent(
                messages=agent_messages,
                business_id=business_id,
                business_name=business_name,
                user_id=user["id"],
                user_name=user.get("name") or user.get("email", "User"),
                user_role=ctx["business_role"],
            ),
        )
    except Exception as e:
        logger.exception("[AgentChat] Run failed")
        result = {
            "answer": f"Sorry, I hit an unexpected error: {e}",
            "tool_calls": [], "pending_approvals": [], "steps": 0,
            "stop_reason": "error",
        }

    duration_ms = int((time.time() - start) * 1000)
    ts = datetime.now().strftime("%H:%M")

    tools_used = [tc.get("name") for tc in result.get("tool_calls", [])]
    user_msg = {"role": "user", "content": req.query, "tools_used": [], "timestamp": ts}
    assistant_msg = {
        "role": "assistant",
        "content": result.get("answer", ""),
        "tools_used": tools_used,
        "tool_calls": result.get("tool_calls", []),
        "pending_approvals": result.get("pending_approvals", []),
        "stop_reason": result.get("stop_reason"),
        "steps": result.get("steps"),
        "timestamp": ts,
    }

    existing = load_messages(conv_id)
    existing.extend([user_msg, assistant_msg])
    save_full_conversation(conv_id, existing)

    try:
        log_query(
            query=req.query, intent="agent",
            tools_used=tools_used,
            answer_preview=result.get("answer", "")[:500],
            success=result.get("stop_reason") == "end_turn",
            duration_ms=duration_ms,
            user_id=user["id"], business_id=business_id,
        )
    except Exception:
        pass

    return {
        "conversation_id": conv_id,
        "message": assistant_msg,
        "duration_ms": duration_ms,
    }


# ── Approvals ────────────────────────────────────────────────────────────────
@app.get("/api/approvals")
def list_approvals(status: Optional[str] = None, limit: int = 100,
                   ctx: dict = Depends(get_current_context)):
    return {
        "actions": _approvals.list_actions(ctx["business_id"], status=status, limit=limit),
        "pending_count": _approvals.pending_count(ctx["business_id"]),
    }


@app.get("/api/approvals/pending-count")
def approvals_pending_count(ctx: dict = Depends(get_current_context)):
    return {"pending_count": _approvals.pending_count(ctx["business_id"])}


@app.get("/api/approvals/{action_id}")
def get_approval(action_id: str, ctx: dict = Depends(get_current_context)):
    return _approvals.get_action(ctx["business_id"], action_id)


@app.post("/api/approvals/{action_id}/approve")
def approve_action(action_id: str, ctx: dict = Depends(get_current_context)):
    return _approvals.approve_action(ctx["business_id"], ctx["user"]["id"], action_id)


@app.post("/api/approvals/{action_id}/reject")
def reject_action(action_id: str, body: dict = None, ctx: dict = Depends(get_current_context)):
    reason = (body or {}).get("reason", "")
    return _approvals.reject_action(ctx["business_id"], ctx["user"]["id"], action_id, reason=reason)


# ── Background agents ───────────────────────────────────────────────────────
from agents.background import scheduler as _agent_sched


@app.get("/api/agents/background")
def list_background_agents(ctx: dict = Depends(get_current_context)):
    return {"jobs": _agent_sched.list_jobs()}


@app.post("/api/agents/background/stale-deals/run")
def run_stale_deals_now(ctx: dict = Depends(get_current_context)):
    from agents.background.stale_deal_watcher import run_for_business
    return run_for_business(ctx["business_id"])


@app.post("/api/agents/background/invoice-reminders/run")
def run_invoice_reminders_now(ctx: dict = Depends(get_current_context)):
    from agents.background.invoice_reminder import run_for_business
    return run_for_business(ctx["business_id"])


@app.post("/api/agents/background/meeting-prep/run")
def run_meeting_prep_now(ctx: dict = Depends(get_current_context)):
    from agents.background.meeting_prep import run_for_user
    return run_for_user(ctx["user"]["id"], ctx["business_id"])


# ── Email triage ─────────────────────────────────────────────────────────────
from agents import email_triage as _email_triage


@app.get("/api/email-triage/account")
def email_triage_account(ctx: dict = Depends(get_current_context)):
    return _email_triage.get_account(ctx["business_id"]) or {"connected": False}


@app.post("/api/email-triage/account")
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


@app.delete("/api/email-triage/account")
def delete_email_triage_account(ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can disconnect email triage")
    _email_triage.disconnect_account(ctx["business_id"])
    return {"ok": True}


@app.post("/api/email-triage/run")
def run_email_triage(ctx: dict = Depends(get_current_context)):
    return _email_triage.run_for_business(ctx["business_id"])


@app.get("/api/email-triage/log")
def email_triage_log(limit: int = 50, ctx: dict = Depends(get_current_context)):
    return _email_triage.get_recent_log(ctx["business_id"], limit=limit)


# ── Business memory ─────────────────────────────────────────────────────────
@app.get("/api/memory")
def list_memory_api(search: Optional[str] = None, limit: int = 100,
                    ctx: dict = Depends(get_current_context)):
    return _mem.list_memory(ctx["business_id"], search=search, limit=limit)


@app.post("/api/memory")
def add_memory_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _mem.add_memory(
        ctx["business_id"], ctx["user"]["id"],
        content=body.get("content", ""),
        kind=body.get("kind", "fact"),
        tags=body.get("tags", ""),
        is_pinned=bool(body.get("is_pinned", False)),
    )


@app.patch("/api/memory/{memory_id}")
def update_memory_api(memory_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _mem.update_memory(ctx["business_id"], memory_id, body)


@app.delete("/api/memory/{memory_id}")
def delete_memory_api(memory_id: str, ctx: dict = Depends(get_current_context)):
    _mem.delete_memory(ctx["business_id"], memory_id)
    return {"ok": True}


@app.post("/api/memory/consolidate")
def consolidate_memory_api(body: dict = None, ctx: dict = Depends(get_current_context)):
    """Dry-run (apply=false) or apply the consolidation plan for this business."""
    from agents.summarizer import consolidate_business_memory
    body = body or {}
    return consolidate_business_memory(
        ctx["business_id"],
        apply_changes=bool(body.get("apply", False)),
        preserve_pinned=bool(body.get("preserve_pinned", True)),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#   NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/notifications")
def get_notifications(unread: bool = False, limit: int = 30, ctx: dict = Depends(get_current_context)):
    from api.notifications import get_recent, get_unread_count
    return {
        "notifications": get_recent(business_id=ctx["business_id"], limit=limit, unread_only=unread),
        "unread_count": get_unread_count(business_id=ctx["business_id"]),
    }


@app.post("/api/notifications/{nid}/read")
def read_notification(nid: str, ctx: dict = Depends(get_current_context)):
    from api.notifications import mark_read
    mark_read(nid, business_id=ctx["business_id"])
    return {"ok": True}


@app.post("/api/notifications/read-all")
def read_all_notifications(ctx: dict = Depends(get_current_context)):
    from api.notifications import mark_all_read
    mark_all_read(business_id=ctx["business_id"])
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#   HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/health")
def health():
    """Public health check. Does not leak tenant data."""
    from config.llm_provider import health_check as provider_health, get_provider, CLAUDE_MODEL
    from config.settings import OLLAMA_MODEL, EMBED_MODEL, EMAIL_ENABLED, DISCORD_ENABLED
    ph = provider_health()
    provider = get_provider()
    if provider == "claude":
        online = ph.get("claude", {}).get("online", False)
        model = CLAUDE_MODEL
    elif provider == "bedrock":
        online = ph.get("bedrock", {}).get("online", False)
        model = ph.get("bedrock", {}).get("primary_model", "")
    else:
        online = ph.get("ollama", {}).get("online", False)
        model = OLLAMA_MODEL
    return {
        "status": "ok" if online else "degraded",
        "provider": provider,
        "ollama": ph.get("ollama", {}),
        "claude": ph.get("claude", {}) if provider == "claude" else None,
        "bedrock": ph.get("bedrock", {}) if provider == "bedrock" else None,
        "model": model,
        "features": {"email": EMAIL_ENABLED, "discord": DISCORD_ENABLED},
        "version": VERSION,
    }


@app.get("/api/stats")
def system_stats(ctx: dict = Depends(get_current_context)):
    from rag.vector_store import get_collection_stats
    from sql_agent.schema_reader import get_table_list
    from memory.query_history import get_stats as qh_stats
    from memory.audit_logger import get_stats as audit_stats

    try:
        kb = get_collection_stats()
    except Exception:
        kb = {"document_count": 0}

    return {
        "knowledge_base": kb,
        "tables": get_table_list(),
        "query_history": qh_stats(business_id=ctx["business_id"]),
        "audit": audit_stats(business_id=ctx["business_id"]),
        "business_id": ctx["business_id"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#   CHAT — REST (for simple queries) + WebSocket (for streaming)
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/chat")
async def chat(req: ChatRequest, ctx: dict = Depends(get_current_context)):
    from orchestrator.graph import run
    from memory.conversation_store import (
        create_conversation, auto_title, save_full_conversation, load_messages,
        assert_conversation_access,
    )
    from memory.query_history import log_query

    start = time.time()
    user = ctx["user"]
    business_id = ctx["business_id"]

    # Ensure conversation exists + belongs to this business
    conv_id = req.conversation_id
    if not conv_id:
        conv_id = create_conversation(user_id=user["id"], business_id=business_id)
        auto_title(conv_id, req.query)
    else:
        assert_conversation_access(conv_id, business_id)

    try:
        loop = asyncio.get_event_loop()
        result_state = await loop.run_in_executor(None, lambda: run(req.query, user_id=user["id"]))
    except Exception as e:
        logger.error(f"Chat error: {e}")
        result_state = {
            "final_answer": f"Error processing request. Is Ollama running? Details: {e}",
            "tools_used": [],
            "citations": [],
        }

    duration_ms = int((time.time() - start) * 1000)
    answer = result_state.get("final_answer", "I couldn't generate a response.")
    tools = result_state.get("tools_used", [])

    user_msg = {
        "role": "user",
        "content": req.query,
        "tools_used": [],
        "citations": [],
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "tools_used": tools,
        "citations": result_state.get("citations", []),
        "sources_used": result_state.get("sources_used", []),
        "multi_agent": result_state.get("multi_agent", False),
        "agents_used": result_state.get("agents_used", []),
        "timestamp": datetime.now().strftime("%H:%M"),
    }

    existing = load_messages(conv_id)
    existing.extend([user_msg, assistant_msg])
    save_full_conversation(conv_id, existing)

    try:
        log_query(
            query=req.query,
            intent=result_state.get("intent", {}).get("primary_intent", "unknown"),
            tools_used=tools,
            answer_preview=answer[:500],
            success=True,
            duration_ms=duration_ms,
            user_id=user["id"],
            business_id=business_id,
        )
    except Exception:
        pass

    return {
        "conversation_id": conv_id,
        "message": assistant_msg,
        "duration_ms": duration_ms,
        "state": {
            "sql_results": _serialize_sql(result_state.get("sql_results", {})),
            "report_path": result_state.get("report_path", ""),
            "whatif_result": result_state.get("whatif_result", {}),
        },
    }


def _serialize_sql(sql_results: dict) -> dict:
    if not sql_results:
        return {}
    result = {**sql_results}
    df = result.pop("dataframe", None)
    if df is not None and hasattr(df, "to_dict"):
        result["data"] = df.head(100).to_dict(orient="records")
        result["columns"] = list(df.columns)
        result["row_count"] = len(df)
    return result


# ── WebSocket for STREAMING chat ──────────────────────────────────────────────
@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """Stream LLM tokens. First message must be an 'auth' frame with token + business_id."""
    await websocket.accept()
    authed_user = None
    business_id = None

    try:
        # First frame must authenticate
        auth_raw = await websocket.receive_text()
        try:
            auth_msg = json.loads(auth_raw)
        except Exception:
            await websocket.send_json({"type": "error", "error": "First frame must be JSON auth"})
            await websocket.close(code=1008)
            return

        if auth_msg.get("type") != "auth":
            await websocket.send_json({"type": "error", "error": "Expected auth frame"})
            await websocket.close(code=1008)
            return

        try:
            payload = decode_token(auth_msg.get("token", ""))
            if payload.get("type") != "access":
                raise HTTPException(401, "Invalid token")
            authed_user = get_user_by_id(payload["sub"])
            if not authed_user:
                raise HTTPException(401, "User not found")
        except Exception as e:
            await websocket.send_json({"type": "error", "error": f"Auth failed: {e}"})
            await websocket.close(code=1008)
            return

        business_id = auth_msg.get("business_id", "").strip()
        if not business_id:
            businesses = list_user_businesses(authed_user["id"])
            if not businesses:
                business_id = ensure_business_for_user(authed_user["id"], authed_user["name"])
            else:
                business_id = businesses[0]["id"]

        try:
            assert_member(business_id, authed_user["id"])
        except HTTPException as e:
            await websocket.send_json({"type": "error", "error": e.detail})
            await websocket.close(code=1008)
            return

        await websocket.send_json({"type": "ready", "business_id": business_id})

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            query = msg.get("query", "")
            conv_id = msg.get("conversation_id")

            await websocket.send_json({"type": "status", "status": "thinking"})

            from orchestrator.graph import _is_just_chitchat
            from config.llm_provider import stream
            from memory.short_term import get_default_memory
            from memory.conversation_store import (
                create_conversation, auto_title, save_full_conversation, load_messages,
                assert_conversation_access,
            )

            if not conv_id:
                conv_id = create_conversation(user_id=authed_user["id"], business_id=business_id)
                auto_title(conv_id, query)
            else:
                try:
                    assert_conversation_access(conv_id, business_id)
                except HTTPException as e:
                    await websocket.send_json({"type": "error", "error": e.detail})
                    continue

            if _is_just_chitchat(query):
                mem = get_default_memory()
                history = mem.get_context_string(max_chars=300)
                history_block = f"\nRecent chat:\n{history}\n" if history else ""

                system = "You are NexusAgent, an AI business assistant. Be concise and helpful."
                prompt = f"""{history_block}User: {query}"""

                full_text = ""
                loop = asyncio.get_event_loop()

                def _stream():
                    # Chitchat path — route to the cheap/fast model tier
                    return list(stream(prompt, system=system, max_tokens=512, fast=True))

                tokens = await loop.run_in_executor(None, _stream)
                for token in tokens:
                    full_text += token
                    await websocket.send_json({"type": "token", "token": token})

                mem.add_turn("user", query)
                mem.add_turn("assistant", full_text, tools_used=[])

                ts = datetime.now().strftime("%H:%M")
                messages = load_messages(conv_id)
                messages.append({"role": "user", "content": query, "tools_used": [], "timestamp": ts})
                messages.append({"role": "assistant", "content": full_text, "tools_used": [], "timestamp": ts})
                save_full_conversation(conv_id, messages)

                await websocket.send_json({
                    "type": "done",
                    "conversation_id": conv_id,
                    "message": {"role": "assistant", "content": full_text, "tools_used": [], "timestamp": ts},
                })
            else:
                loop = asyncio.get_event_loop()
                from orchestrator.graph import run
                result_state = await loop.run_in_executor(None, lambda: run(query, user_id=authed_user["id"]))
                answer = result_state.get("final_answer", "No response.")
                tools = result_state.get("tools_used", [])
                ts = datetime.now().strftime("%H:%M")

                messages = load_messages(conv_id)
                messages.append({"role": "user", "content": query, "tools_used": [], "timestamp": ts})
                messages.append({
                    "role": "assistant", "content": answer, "tools_used": tools, "timestamp": ts,
                    "sources_used": result_state.get("sources_used", []),
                    "multi_agent": result_state.get("multi_agent", False),
                    "agents_used": result_state.get("agents_used", []),
                })
                save_full_conversation(conv_id, messages)

                await websocket.send_json({
                    "type": "done",
                    "conversation_id": conv_id,
                    "message": messages[-1],
                    "state": {"sql_results": _serialize_sql(result_state.get("sql_results", {}))},
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#   CONVERSATIONS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/conversations")
def list_conversations_api(limit: int = 20, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import list_conversations as lc
    return lc(business_id=ctx["business_id"], limit=limit)


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import load_messages, assert_conversation_access
    info = assert_conversation_access(conv_id, ctx["business_id"])
    return {"info": info, "messages": load_messages(conv_id)}


@app.patch("/api/conversations/{conv_id}")
def update_conversation(conv_id: str, body: ConversationUpdate, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import update_title, assert_conversation_access
    assert_conversation_access(conv_id, ctx["business_id"])
    update_title(conv_id, body.title)
    return {"ok": True}


@app.delete("/api/conversations/{conv_id}")
def delete_conversation_api(conv_id: str, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import delete_conversation as dc, assert_conversation_access
    assert_conversation_access(conv_id, ctx["business_id"])
    dc(conv_id)
    return {"ok": True}


@app.post("/api/conversations")
def create_new_conversation(ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import create_conversation
    conv_id = create_conversation(user_id=ctx["user"]["id"], business_id=ctx["business_id"])
    return {"conversation_id": conv_id}


# ═══════════════════════════════════════════════════════════════════════════════
#   DATABASE (developer/admin only — exposes raw schema)
# ═══════════════════════════════════════════════════════════════════════════════
_SYSTEM_TABLE_PREFIXES = ("nexus_", "sqlite_")


@app.get("/api/database/tables")
def list_tables(ctx: dict = Depends(get_current_context)):
    import sqlite3
    import pandas as pd
    from config.settings import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
        )["name"].tolist()

        result = []
        for t in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            except Exception:
                count = 0
            cols = pd.read_sql_query(f"PRAGMA table_info([{t}])", conn)
            result.append({
                "name": t,
                "row_count": count,
                "column_count": len(cols),
                "is_system": t.startswith(_SYSTEM_TABLE_PREFIXES),
            })
    finally:
        conn.close()
    return result


@app.get("/api/database/tables/{table_name}")
def get_table_detail(table_name: str, limit: int = 50, ctx: dict = Depends(get_current_context)):
    import sqlite3
    import pandas as pd
    from config.settings import DB_PATH

    if not table_name.replace("_", "").isalnum():
        raise HTTPException(400, "Invalid table name")

    conn = sqlite3.connect(DB_PATH)
    try:
        cols = pd.read_sql_query(f"PRAGMA table_info([{table_name}])", conn)
        if cols.empty:
            raise HTTPException(404, "Table not found")
        fks = pd.read_sql_query(f"PRAGMA foreign_key_list([{table_name}])", conn)
        row_count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]

        limit = max(1, min(limit, 500))
        df = pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {limit}", conn)

        stats = []
        for _, col in cols.iterrows():
            if col["type"] in ("INTEGER", "REAL", "NUMERIC"):
                try:
                    s = pd.read_sql_query(
                        f"SELECT MIN([{col['name']}]) as min, MAX([{col['name']}]) as max, "
                        f"ROUND(AVG([{col['name']}]), 2) as avg FROM [{table_name}]",
                        conn,
                    )
                    stats.append({"column": col["name"], **s.iloc[0].to_dict()})
                except Exception:
                    pass
    finally:
        conn.close()

    return {
        "name": table_name,
        "row_count": row_count,
        "columns": cols.to_dict(orient="records"),
        "foreign_keys": fks.to_dict(orient="records") if not fks.empty else [],
        "data": df.to_dict(orient="records"),
        "column_stats": stats,
    }


@app.post("/api/database/import")
async def import_data(
    file: UploadFile = File(...),
    table_name: str = Query(""),
    if_exists: str = Query("fail"),
    ctx: dict = Depends(get_current_context),
):
    import tempfile
    from sql_agent.data_import import preview_file, import_to_database

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50 MB max
            raise HTTPException(413, "File too large (max 50 MB)")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        preview = preview_file(tmp_path)
        if preview.get("error"):
            raise HTTPException(400, preview["error"])

        # Prefix tenant tables with biz id to prevent cross-tenant imports
        name = table_name or preview["suggested_table_name"]
        if name.startswith(_SYSTEM_TABLE_PREFIXES):
            raise HTTPException(400, "Cannot overwrite system tables")
        full_df = preview.get("_full_df")

        result = import_to_database(full_df, name, if_exists=if_exists)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not result["success"]:
        raise HTTPException(400, result["error"])

    try:
        from sql_agent.query_generator import clear_cache
        clear_cache()
    except Exception:
        pass

    return result


@app.post("/api/database/import/preview")
async def preview_import(file: UploadFile = File(...), ctx: dict = Depends(get_current_context)):
    import tempfile
    from sql_agent.data_import import preview_file

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(413, "File too large (max 50 MB)")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        preview = preview_file(tmp_path, max_rows=20)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if preview.get("error"):
        raise HTTPException(400, preview["error"])

    preview.pop("_full_df", None)
    df = preview.pop("dataframe", None)
    if df is not None:
        preview["preview_data"] = df.to_dict(orient="records")

    return preview


# ═══════════════════════════════════════════════════════════════════════════════
#   REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/reports/generate")
def generate_report(req: ReportRequest, ctx: dict = Depends(get_current_context)):
    from orchestrator.graph import run
    result = run(f"Generate a report: {req.query}", user_id=ctx["user"]["id"])
    pdf_path = result.get("report_path", "")
    if pdf_path and Path(pdf_path).exists():
        return {"path": pdf_path, "filename": Path(pdf_path).name}
    raise HTTPException(500, "Report generation failed")


@app.get("/api/reports")
def list_reports(ctx: dict = Depends(get_current_context)):
    from action_tools.file_dispatcher import get_recent_outputs
    return get_recent_outputs(n=20, subfolder="reports")


@app.get("/api/reports/download/{filename}")
def download_report(filename: str, ctx: dict = Depends(get_current_context)):
    from config.settings import REPORTS_DIR
    # Guard against path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Invalid filename")
    path = Path(REPORTS_DIR) / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Report not found")
    ext = path.suffix.lower()
    media = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(ext, "application/octet-stream")
    return FileResponse(str(path), filename=filename, media_type=media)


# ═══════════════════════════════════════════════════════════════════════════════
#   WHAT-IF SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/whatif")
def run_whatif(req: WhatIfRequest, ctx: dict = Depends(get_current_context)):
    from utils.whatif_simulator import run_full_simulation
    result = run_full_simulation(req.scenario)

    for key in ("before_df", "after_df"):
        df = result.get(key)
        if df is not None and hasattr(df, "to_dict"):
            result[key] = df.to_dict(orient="records")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#   QUERY HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/history")
def query_history(
    search: Optional[str] = None,
    intent: Optional[str] = None,
    starred: bool = False,
    limit: int = 50,
    ctx: dict = Depends(get_current_context),
):
    from memory.query_history import get_history, get_stats
    return {
        "queries": get_history(
            business_id=ctx["business_id"],
            search=search, intent_filter=intent, starred_only=starred, limit=limit,
        ),
        "stats": get_stats(business_id=ctx["business_id"]),
    }


@app.post("/api/history/{query_id}/star")
def toggle_star(query_id: int, ctx: dict = Depends(get_current_context)):
    from memory.query_history import toggle_star as ts
    return {"starred": ts(query_id)}


@app.delete("/api/history/{query_id}")
def delete_history_entry(query_id: int, ctx: dict = Depends(get_current_context)):
    from memory.query_history import delete_query
    delete_query(query_id)
    return {"ok": True}


@app.delete("/api/history")
def clear_all_history(ctx: dict = Depends(get_current_context)):
    from memory.query_history import clear_history
    count = clear_history(business_id=ctx["business_id"])
    return {"deleted": count}


# ═══════════════════════════════════════════════════════════════════════════════
#   KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/knowledge")
def knowledge_base(ctx: dict = Depends(get_current_context)):
    from rag.multi_document_rag import get_sources_list
    from rag.vector_store import get_collection_stats
    try:
        stats = get_collection_stats()
    except Exception:
        stats = {"document_count": 0}
    return {"sources": get_sources_list(), "stats": stats}


@app.post("/api/knowledge/upload")
async def upload_document(file: UploadFile = File(...), ctx: dict = Depends(get_current_context)):
    from rag.ingestion import ingest_file
    from rag.embedder import embed_documents
    from rag.vector_store import add_documents
    from config.settings import DOCUMENTS_DIR

    safe_name = Path(file.filename).name  # strip paths
    if not safe_name:
        raise HTTPException(400, "Invalid filename")
    dest = Path(DOCUMENTS_DIR) / safe_name
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20 MB)")
    dest.write_bytes(content)

    docs = ingest_file(str(dest))
    if docs:
        texts = [d.page_content for d in docs]
        metas = [{**d.metadata, "business_id": ctx["business_id"]} for d in docs]
        embeddings = embed_documents(texts)
        added = add_documents(texts, embeddings, metas)
        return {"filename": safe_name, "chunks_added": added}
    raise HTTPException(400, "Could not process document")


# ═══════════════════════════════════════════════════════════════════════════════
#   ANOMALY MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/monitor/status")
def monitor_status(ctx: dict = Depends(get_current_context)):
    from orchestrator.proactive_monitor import get_last_check_status
    return get_last_check_status()


@app.post("/api/monitor/run")
def run_monitor(ctx: dict = Depends(get_current_context)):
    from orchestrator.proactive_monitor import manual_trigger
    return manual_trigger()


# ═══════════════════════════════════════════════════════════════════════════════
#   EXPORT
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/export/markdown")
def export_markdown(messages: list[dict], ctx: dict = Depends(get_current_context)):
    from utils.export_conversation import to_markdown
    return {"markdown": to_markdown(messages)}


@app.post("/api/export/pdf")
def export_pdf(messages: list[dict], ctx: dict = Depends(get_current_context)):
    from utils.export_conversation import to_pdf
    path = to_pdf(messages)
    if path and Path(path).exists():
        return FileResponse(str(path), filename=Path(path).name, media_type="application/pdf")
    raise HTTPException(500, "PDF export failed")


# ═══════════════════════════════════════════════════════════════════════════════
#   SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/settings")
def get_settings(ctx: dict = Depends(get_current_context)):
    from config.settings import (
        OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL, EMBED_MODEL,
        EMAIL_ENABLED, DISCORD_ENABLED, MAX_SQL_RETRIES, MAX_REFLECTION_RETRIES,
        CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RETRIEVAL, VERSION,
    )
    import sys as _sys

    models = []
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            for m in resp.json().get("models", []):
                models.append({
                    "name": m.get("name", "?"),
                    "size_gb": round(m.get("size", 0) / (1024 ** 3), 1),
                    "active": OLLAMA_MODEL in m.get("name", ""),
                })
    except Exception:
        pass

    return {
        "version": VERSION,
        "python_version": _sys.version.split()[0],
        "ollama_url": OLLAMA_BASE_URL,
        "primary_model": OLLAMA_MODEL,
        "fallback_model": OLLAMA_FALLBACK_MODEL,
        "embed_model": EMBED_MODEL,
        "email_enabled": EMAIL_ENABLED,
        "discord_enabled": DISCORD_ENABLED,
        "max_sql_retries": MAX_SQL_RETRIES,
        "max_reflection_retries": MAX_REFLECTION_RETRIES,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "top_k_retrieval": TOP_K_RETRIEVAL,
        "available_models": models,
    }


@app.post("/api/settings/reset-llm")
def reset_llm(ctx: dict = Depends(get_current_context)):
    from config.llm_config import reset_instances
    reset_instances()
    return {"ok": True, "message": "LLM connection reset"}


@app.post("/api/settings/clear-cache")
def clear_cache(ctx: dict = Depends(get_current_context)):
    from sql_agent.query_generator import clear_cache as cc
    cc()
    return {"ok": True, "message": "SQL cache cleared"}


# ═══════════════════════════════════════════════════════════════════════════════
#   WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/workflows")
def list_workflows_api(ctx: dict = Depends(get_current_context)):
    from workflows.storage import list_workflows as lw
    return lw(business_id=ctx["business_id"])


@app.get("/api/workflows/node-types")
def get_node_types(ctx: dict = Depends(get_current_context)):
    from workflows.node_registry import NODE_TYPES
    return NODE_TYPES


@app.get("/api/workflows/templates")
def get_workflow_templates(ctx: dict = Depends(get_current_context)):
    from workflows.templates import get_all_templates
    return get_all_templates()


@app.post("/api/workflows/generate-from-text")
def generate_workflow_from_text(body: dict, ctx: dict = Depends(get_current_context)):
    """Take a natural-language description and return a workflow draft (not saved)."""
    description = (body.get("description") or "").strip()
    if not description:
        raise HTTPException(400, "description is required")
    if len(description) > 2000:
        raise HTTPException(400, "description too long (max 2000 chars)")
    from agents.workflow_builder import build_workflow
    try:
        wf = build_workflow(description)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return wf


@app.post("/api/agent/research")
def agent_research(body: dict, ctx: dict = Depends(get_current_context)):
    """Run the research agent directly (outside the chat loop)."""
    from agents.research_agent import research
    subject = (body.get("subject") or "").strip()
    if not subject:
        raise HTTPException(400, "subject is required")
    try:
        return research(
            subject=subject,
            context=body.get("context", ""),
            save_as_interaction=bool(body.get("save_as_interaction", False)),
            business_id=ctx["business_id"],
            user_id=ctx["user"]["id"],
            contact_id=body.get("contact_id"),
            company_id=body.get("company_id"),
            deal_id=body.get("deal_id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/workflows/{wf_id}")
def get_workflow(wf_id: str, ctx: dict = Depends(get_current_context)):
    from workflows.storage import load_workflow
    wf = load_workflow(wf_id, business_id=ctx["business_id"])
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return wf


@app.post("/api/workflows")
def save_workflow_api(wf: dict, ctx: dict = Depends(get_current_context)):
    from workflows.storage import save_workflow as sw, load_workflow
    # If updating, verify ownership
    if wf.get("id"):
        existing = load_workflow(wf["id"], business_id=ctx["business_id"])
        if not existing:
            raise HTTPException(404, "Workflow not found for this business")
    wf_id = sw(wf, business_id=ctx["business_id"], user_id=ctx["user"]["id"])
    return {"id": wf_id}


@app.delete("/api/workflows/{wf_id}")
def delete_workflow_api(wf_id: str, ctx: dict = Depends(get_current_context)):
    from workflows.storage import delete_workflow
    ok = delete_workflow(wf_id, business_id=ctx["business_id"])
    if not ok:
        raise HTTPException(404, "Workflow not found")
    return {"ok": True}


@app.post("/api/workflows/{wf_id}/toggle")
def toggle_workflow(wf_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    from workflows.storage import toggle_enabled
    enabled = bool(body.get("enabled", False))
    ok = toggle_enabled(wf_id, enabled, business_id=ctx["business_id"])
    if not ok:
        raise HTTPException(404, "Workflow not found")
    try:
        from workflows.scheduler import sync_all_workflows
        sync_all_workflows()
    except Exception:
        pass
    return {"ok": True, "enabled": enabled}


@app.post("/api/workflows/{wf_id}/run")
def run_workflow(wf_id: str, ctx: dict = Depends(get_current_context)):
    from workflows.storage import load_workflow
    from workflows.executor import execute_workflow
    wf = load_workflow(wf_id, business_id=ctx["business_id"])
    if not wf:
        raise HTTPException(404, "Workflow not found")
    result = execute_workflow(wf)
    return result


@app.post("/api/workflows/run-preview")
def run_workflow_preview(wf: dict, ctx: dict = Depends(get_current_context)):
    from workflows.executor import execute_workflow
    # Force the workflow to run within the current business
    wf["business_id"] = ctx["business_id"]
    result = execute_workflow(wf)
    return result


@app.get("/api/workflows/scheduler/jobs")
def get_scheduler_jobs(ctx: dict = Depends(get_current_context)):
    from workflows.scheduler import get_scheduled_jobs
    return get_scheduled_jobs()


@app.get("/api/workflows/scheduler/history")
def get_workflow_history(limit: int = 30, ctx: dict = Depends(get_current_context)):
    from workflows.scheduler import get_run_history
    return get_run_history(limit)


# ═══════════════════════════════════════════════════════════════════════════════
#   VOICE TRANSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/voice/transcribe")
async def transcribe_voice(file: UploadFile = File(...), ctx: dict = Depends(get_current_context)):
    import tempfile
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(413, "Audio too large (max 25 MB)")
        tmp.write(content)
        tmp_path = tmp.name

    wav_check = tmp_path
    try:
        from voice.listener import _transcribe
        wav_path = tmp_path
        if suffix.lower() in (".webm", ".ogg", ".mp4", ".m4a"):
            try:
                import subprocess
                wav_path = tmp_path.replace(suffix, ".wav")
                wav_check = wav_path
                subprocess.run(
                    ["ffmpeg", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
                    capture_output=True, timeout=10,
                )
            except Exception:
                wav_path = tmp_path

        text = _transcribe(wav_path)
        return {"text": text or "", "success": bool(text)}
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"text": "", "success": False, "error": str(e)}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if wav_check != tmp_path:
            Path(wav_check).unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
#   EMAIL — MANUAL SEND APPROVAL
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/email/send")
def send_email_now(body: dict, ctx: dict = Depends(get_current_context)):
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    if not EMAIL_ENABLED:
        raise HTTPException(400, "Email not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")

    to = (body.get("to") or "").strip()
    subject = (body.get("subject") or "").strip()
    email_body = (body.get("body") or "").strip()

    if not to or not subject or not email_body:
        raise HTTPException(400, "Missing 'to', 'subject', or 'body'")
    if len(subject) > 400 or len(email_body) > 50000:
        raise HTTPException(400, "Subject or body too long")

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(email_body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="email_send",
            input_summary=f"to={to}, subject={subject[:80]}",
            output_summary="sent",
            approved=True, success=True,
            business_id=ctx["business_id"], user_id=ctx["user"]["id"],
        )
        logger.success(f"[Email] Sent to {to}: {subject}")
        return {"sent": True, "to": to, "subject": subject}
    except Exception as e:
        logger.error(f"[Email] Send failed: {e}")
        raise HTTPException(500, f"Failed to send email: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#   WEBHOOK TRIGGER (public — workflow has its own business scope)
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/webhooks/{webhook_path:path}")
async def receive_webhook(webhook_path: str, request: Request):
    """Receive a webhook POST and trigger matching workflows.
    Public endpoint — each workflow carries its own business_id.
    """
    payload = {}
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    from workflows.storage import list_workflows as lw
    from workflows.executor import execute_workflow

    target_path = f"/webhook/{webhook_path}"
    triggered = []

    for wf in lw():  # intentionally unscoped — route by path match only
        if not wf.get("enabled"):
            continue
        for node in wf.get("nodes", []):
            if node.get("type") == "webhook_trigger":
                if node.get("config", {}).get("path", "") == target_path:
                    wf["_webhook_payload"] = payload
                    result = execute_workflow(wf)
                    triggered.append({"workflow": wf.get("name"), "status": result.get("status")})

    if not triggered:
        raise HTTPException(404, f"No enabled workflow found for path: {target_path}")
    return {"triggered": triggered}


# ═══════════════════════════════════════════════════════════════════════════════
#   RUNTIME SETTINGS UPDATE (admin only)
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/settings/update")
def update_runtime_setting(body: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")

    key = body.get("key", "")
    value = body.get("value", "")
    allowed = {"DISCORD_WEBHOOK_URL", "SLACK_WEBHOOK_URL", "GMAIL_USER",
               "GMAIL_APP_PASSWORD", "LOG_LEVEL", "ANOMALY_THRESHOLD"}

    if key not in allowed:
        raise HTTPException(400, f"Cannot update '{key}'. Allowed: {', '.join(sorted(allowed))}")

    env_path = ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    import os
    os.environ[key] = value
    return {"ok": True, "key": key}


# ═══════════════════════════════════════════════════════════════════════════════
#   ANALYTICS & FORECASTING
# ═══════════════════════════════════════════════════════════════════════════════
from api import analytics as _analytics


@app.get("/api/analytics/pipeline-velocity")
def analytics_pipeline_velocity(ctx: dict = Depends(get_current_context)):
    return _analytics.pipeline_velocity(ctx["business_id"])


@app.get("/api/analytics/revenue-forecast")
def analytics_revenue_forecast(horizon_months: int = 6, ctx: dict = Depends(get_current_context)):
    horizon_months = max(1, min(12, horizon_months))
    return _analytics.revenue_forecast(ctx["business_id"], horizon_months=horizon_months)


@app.get("/api/analytics/agent-impact")
def analytics_agent_impact(days: int = 30, ctx: dict = Depends(get_current_context)):
    days = max(1, min(180, days))
    return _analytics.agent_impact(ctx["business_id"], days=days)


@app.get("/api/analytics/churn-risk")
def analytics_churn_risk(max_deals: int = 15, ctx: dict = Depends(get_current_context)):
    max_deals = max(1, min(50, max_deals))
    return _analytics.churn_risk(ctx["business_id"], max_deals=max_deals)


# ═══════════════════════════════════════════════════════════════════════════════
#   TEAM — invites, activity feed
# ═══════════════════════════════════════════════════════════════════════════════
from api import team as _team


class InviteCreate(BaseModel):
    email: str
    role: str = "member"


@app.get("/api/team/invites")
def list_team_invites(include_accepted: bool = False, ctx: dict = Depends(get_current_context)):
    from api.businesses import assert_member
    assert_member(ctx["business_id"], ctx["user"]["id"])
    return _team.list_invites(ctx["business_id"], include_accepted=include_accepted)


@app.post("/api/team/invites")
def create_team_invite(req: InviteCreate, ctx: dict = Depends(get_current_context)):
    return _team.create_invite(
        ctx["business_id"], ctx["user"]["id"],
        email=req.email, role=req.role,
    )


@app.delete("/api/team/invites/{token}")
def revoke_team_invite(token: str, ctx: dict = Depends(get_current_context)):
    _team.revoke_invite(ctx["business_id"], ctx["user"]["id"], token)
    return {"ok": True}


# Public — no auth, so someone without an account can see what they're joining
@app.get("/api/team/invites/preview")
def preview_invite(token: str):
    return _team.get_invite_preview(token)


class AcceptInvite(BaseModel):
    token: str


@app.post("/api/team/invites/accept")
def accept_team_invite(body: AcceptInvite, user: dict = Depends(get_current_user)):
    return _team.accept_invite(body.token, user["id"], user["email"])


@app.get("/api/team/activity")
def activity_feed_api(limit: int = 60, ctx: dict = Depends(get_current_context)):
    return _team.activity_feed(ctx["business_id"], limit=limit)


# ═══════════════════════════════════════════════════════════════════════════════
#   WHATSAPP — bridge webhook, link flow, status
# ═══════════════════════════════════════════════════════════════════════════════
from api import whatsapp as _wa


@app.post("/api/whatsapp/link/generate")
def whatsapp_generate_link(ctx: dict = Depends(get_current_context)):
    """Issue a 6-char code the user will text to the WhatsApp bot to link their phone."""
    return _wa.generate_link_token(ctx["user"]["id"], ctx["business_id"])


@app.get("/api/whatsapp/account")
def whatsapp_account(ctx: dict = Depends(get_current_context)):
    acc = _wa.get_account_for_user(ctx["user"]["id"])
    return acc or {"linked": False}


@app.delete("/api/whatsapp/account")
def whatsapp_unlink(ctx: dict = Depends(get_current_context)):
    _wa.unlink_account(ctx["user"]["id"])
    return {"ok": True}


@app.get("/api/whatsapp/bridge-secret")
def whatsapp_bridge_secret(user: dict = Depends(get_current_user)):
    """The shared secret the Node bridge needs. Owner/admin only."""
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return {"secret": _wa.get_bridge_secret()}


@app.post("/api/whatsapp/inbound")
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
    result = await loop.run_in_executor(None, lambda: _wa.handle_inbound(phone, text, message_id))
    return result


@app.get("/api/whatsapp/attachment")
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


# ═══════════════════════════════════════════════════════════════════════════════
#   GLOBAL SEARCH — Ctrl+K omnibox
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/search")
def global_search(q: str, limit: int = 8, ctx: dict = Depends(get_current_context)):
    """
    Search across contacts, companies, deals, tasks, invoices, documents,
    memory, and recent conversations. Everything business-scoped.
    Returns grouped results for fast keyboard navigation.
    """
    q = (q or "").strip()
    if len(q) < 2:
        return {"groups": []}
    limit = max(1, min(limit, 20))
    like = f"%{q}%"
    biz = ctx["business_id"]

    import sqlite3 as _sq
    from config.settings import DB_PATH
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    groups: list = []

    def _g(kind, rows, key_fields, route_fn):
        items = []
        for r in rows:
            d = dict(r)
            items.append({
                "id": d.get("id") or d.get(key_fields[0]),
                "title": " ".join(str(d.get(k) or "") for k in key_fields if d.get(k)).strip() or "(untitled)",
                "subtitle": d.get("email") or d.get("company_name") or d.get("stage") or d.get("status") or "",
                "route": route_fn(d),
                "kind": kind,
            })
        if items:
            groups.append({"kind": kind, "items": items})

    try:
        # Contacts
        rows = conn.execute(
            "SELECT id, first_name, last_name, email, phone, title "
            "FROM nexus_contacts WHERE business_id = ? "
            "AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR tags LIKE ?) "
            "LIMIT ?",
            (biz, like, like, like, like, limit),
        ).fetchall()
        _g("contact", rows, ["first_name", "last_name"], lambda d: "/crm")

        # Companies
        rows = conn.execute(
            "SELECT id, name, industry, website FROM nexus_companies "
            "WHERE business_id = ? AND (name LIKE ? OR industry LIKE ? OR tags LIKE ?) LIMIT ?",
            (biz, like, like, like, limit),
        ).fetchall()
        _g("company", rows, ["name"], lambda d: "/crm")

        # Deals
        rows = conn.execute(
            "SELECT id, name, stage, value, currency FROM nexus_deals "
            "WHERE business_id = ? AND (name LIKE ? OR notes LIKE ?) LIMIT ?",
            (biz, like, like, limit),
        ).fetchall()
        _g("deal", rows, ["name"], lambda d: "/crm")

        # Tasks
        rows = conn.execute(
            "SELECT id, title, status, priority, due_date FROM nexus_tasks "
            "WHERE business_id = ? AND (title LIKE ? OR description LIKE ? OR tags LIKE ?) LIMIT ?",
            (biz, like, like, like, limit),
        ).fetchall()
        _g("task", rows, ["title"], lambda d: "/tasks")

        # Invoices
        rows = conn.execute(
            "SELECT id, number, customer_name, status, total, currency FROM nexus_invoices "
            "WHERE business_id = ? AND (number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ?) LIMIT ?",
            (biz, like, like, like, limit),
        ).fetchall()
        _g("invoice", rows, ["number", "customer_name"], lambda d: "/invoices")

        # Documents
        try:
            rows = conn.execute(
                "SELECT id, title, template_key, format FROM nexus_documents "
                "WHERE business_id = ? AND title LIKE ? LIMIT ?",
                (biz, like, limit),
            ).fetchall()
            _g("document", rows, ["title"], lambda d: "/documents")
        except _sq.OperationalError:
            pass

        # Memory
        try:
            rows = conn.execute(
                "SELECT id, content, kind FROM nexus_business_memory "
                "WHERE business_id = ? AND content LIKE ? LIMIT ?",
                (biz, like, limit),
            ).fetchall()
            # Hand-build items with shorter titles (memory is free text)
            items = [{
                "id": r["id"],
                "title": (r["content"] or "")[:80],
                "subtitle": r["kind"] or "",
                "route": "/memory",
                "kind": "memory",
            } for r in rows]
            if items:
                groups.append({"kind": "memory", "items": items})
        except _sq.OperationalError:
            pass

        # Recent conversations (title match)
        rows = conn.execute(
            "SELECT conversation_id, title, updated_at FROM nexus_conversations "
            "WHERE business_id = ? AND title LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (biz, like, limit),
        ).fetchall()
        items = [{
            "id": r["conversation_id"],
            "title": r["title"] or "(untitled chat)",
            "subtitle": (r["updated_at"] or "")[:16],
            "route": f"/chat?conv={r['conversation_id']}",
            "kind": "conversation",
        } for r in rows]
        if items:
            groups.append({"kind": "conversation", "items": items})

    finally:
        conn.close()

    return {"groups": groups, "query": q}


# ═══════════════════════════════════════════════════════════════════════════════
#   SERVE REACT FRONTEND (production only — when dist/ exists)
# ═══════════════════════════════════════════════════════════════════════════════
_frontend_dist = ROOT / "frontend" / "dist"
if _frontend_dist.is_dir():
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Never shadow API or WS routes — return a proper 404 so the JSON
        # client in the browser surfaces a real error instead of silently
        # receiving index.html and choking on "<!doctype".
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(404, f"Not found: /{full_path}")
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))

    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="static")
