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

# Apply composite indexes on frequently filtered columns (idempotent).
try:
    from api.db_indexes import apply_indexes
    apply_indexes()
except Exception as e:
    logger.warning(f"Index pass failed: {e}")

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

# Per-IP rate limiter — rejects after 120 req/min default, tighter on
# /api/voice (20/min) and /api/auth (30/min).
from api.reliability import rate_limit_middleware as _rate_limit_middleware
app.middleware("http")(_rate_limit_middleware)


# ── Pydantic Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None


class WhatIfRequest(BaseModel):
    scenario: str = Field(..., min_length=1, max_length=2000)


class ReportRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


# ── Auth Setup ────────────────────────────────────────────────────────────────
from api.auth import (
    ensure_default_admin, decode_token,
    get_current_user, get_current_context, get_user_by_id,
)
from api.businesses import (
    list_user_businesses, assert_member,
    ensure_business_for_user, migrate_legacy_data,
)

ensure_default_admin()
migrate_legacy_data()


# Auth + 2FA + sessions endpoints live in api/routers/auth.py.
# Audit log endpoints live in api/routers/audit.py.
# Agents + custom agents + schedule + nudges live in api/routers/agents.py.


# Morning briefing endpoints live in api/routers/briefing.py.

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


# Privacy / cloud-LLM audit endpoints live in api/routers/privacy.py.


# Onboarding endpoints live in api/routers/onboarding.py.
# Notifications + prefs live in api/routers/notifications.py.
# Tags + workspace export live in api/routers/tags.py.


# Password-reset endpoints (forgot/reset) live in api/routers/auth.py.


# Businesses + members live in api/routers/businesses.py.
# CRM lives in api/routers/crm.py.
# Integrations + webhook receiver live in api/routers/integrations.py.
# RAG collections + document expiry live in api/routers/rag.py.


# Saved queries, suggestions extracted to api/routers/.


# ═══════════════════════════════════════════════════════════════════════════════
#   Research agent — structured reports + save to knowledge base (2.9)
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/research/structured")
def research_structured(body: dict, ctx: dict = Depends(get_current_context)):
    from agents.research_agent import structured_research
    subject = (body.get("subject") or "").strip()
    if not subject:
        raise HTTPException(400, "subject is required")
    try:
        return structured_research(subject, context=(body.get("context") or ""))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/research/save-to-kb")
def research_save_to_kb(body: dict, ctx: dict = Depends(get_current_context)):
    """Save a structured research report into the RAG knowledge base."""
    from agents.research_agent import save_report_to_kb
    report = body.get("report") or {}
    if not report.get("subject"):
        raise HTTPException(400, "report.subject is required")
    return save_report_to_kb(ctx["business_id"], report)


@app.get("/api/activity/{entity_type}/{entity_id}")
def activity_timeline_api(entity_type: str, entity_id: str, limit: int = 200,
                          ctx: dict = Depends(get_current_context)):
    """Per-record activity timeline — tags, tasks, invoices, tool calls."""
    from api import activity_feed
    try:
        return {"events": activity_feed.timeline(
            ctx["business_id"], entity_type, entity_id, limit=limit,
        )}
    except ValueError as e:
        raise HTTPException(400, str(e))


# Tasks, invoices, documents live in their routers under api/routers/.


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

    from config import privacy as _privacy
    _privacy.reset_stats()
    # Honor the per-conversation lock — if the user toggled "treat as sensitive",
    # every LLM call in this request is forced local.
    from memory.conversation_store import is_sensitive as _is_sensitive
    _privacy.set_sensitive_context(_is_sensitive(conv_id))

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

    privacy_stats = _privacy.get_stats()
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
        "privacy": privacy_stats,
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
#   Modular routers — see api/routers/ for per-domain endpoint groups.
# ═══════════════════════════════════════════════════════════════════════════════
from api.routers import (
    setup         as _r_setup,
    admin         as _r_admin,
    tags          as _r_tags,
    integrations  as _r_integrations,
    suggestions   as _r_suggestions,
    saved_queries as _r_saved_queries,
    errors        as _r_errors,
    agents        as _r_agents,
    crm           as _r_crm,
    tasks         as _r_tasks,
    invoices      as _r_invoices,
    documents     as _r_documents,
    briefing      as _r_briefing,
    privacy       as _r_privacy,
    conversations as _r_conversations,
    auth          as _r_auth,
    businesses    as _r_businesses,
    rag           as _r_rag,
    audit         as _r_audit,
    onboarding    as _r_onboarding,
    notifications as _r_notifications,
)
for _r in (_r_setup, _r_admin, _r_tags, _r_integrations,
           _r_suggestions, _r_saved_queries, _r_errors, _r_agents,
           _r_crm, _r_tasks, _r_invoices, _r_documents,
           _r_briefing, _r_privacy, _r_conversations, _r_auth,
           _r_businesses, _r_rag, _r_audit, _r_onboarding, _r_notifications):
    app.include_router(_r.router)


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

    from config import privacy as _privacy
    _privacy.reset_stats()

    # Ensure conversation exists + belongs to this business
    conv_id = req.conversation_id
    if not conv_id:
        conv_id = create_conversation(user_id=user["id"], business_id=business_id)
        auto_title(conv_id, req.query)
    else:
        assert_conversation_access(conv_id, business_id)

    from memory.conversation_store import is_sensitive as _is_sensitive
    _privacy.set_sensitive_context(_is_sensitive(conv_id))

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
        "privacy": _privacy.get_stats(),
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

            from config import privacy as _privacy
            _privacy.reset_stats()

            from orchestrator.graph import _is_just_chitchat
            from config.llm_provider import stream
            from memory.short_term import get_default_memory
            from memory.conversation_store import (
                create_conversation, auto_title, save_full_conversation, load_messages,
                assert_conversation_access, is_sensitive as _is_sensitive,
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

            _privacy.set_sensitive_context(_is_sensitive(conv_id))

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
                privacy_stats = _privacy.get_stats()
                messages = load_messages(conv_id)
                messages.append({"role": "user", "content": query, "tools_used": [], "timestamp": ts})
                messages.append({
                    "role": "assistant", "content": full_text, "tools_used": [],
                    "timestamp": ts, "privacy": privacy_stats,
                })
                save_full_conversation(conv_id, messages)

                await websocket.send_json({
                    "type": "done",
                    "conversation_id": conv_id,
                    "message": {
                        "role": "assistant", "content": full_text, "tools_used": [],
                        "timestamp": ts, "privacy": privacy_stats,
                    },
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
                    "privacy": _privacy.get_stats(),
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


# Conversation CRUD endpoints live in api/routers/conversations.py.


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


# ═══════════════════════════════════════════════════════════════════════════════
#   Entity import wizard — CSV/Excel → contacts/tasks/invoices with column mapping
# ═══════════════════════════════════════════════════════════════════════════════
_ENTITY_IMPORT_STASH: dict = {}   # session_id → (path, expires_ts)
_ENTITY_IMPORT_TTL = 15 * 60       # 15 minutes


def _prune_import_stash():
    now = time.time()
    expired = [k for k, (_, exp) in _ENTITY_IMPORT_STASH.items() if exp < now]
    for k in expired:
        p, _ = _ENTITY_IMPORT_STASH.pop(k, (None, 0))
        if p:
            Path(p).unlink(missing_ok=True)


@app.post("/api/entity-import/preview")
async def entity_import_preview(
    file: UploadFile = File(...),
    entity_type: str = Query(...),
    ctx: dict = Depends(get_current_context),
):
    """Upload CSV/Excel + entity_type → get sample rows + auto-suggested mapping."""
    import tempfile, uuid as _uuid
    from api import entity_import

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(413, "File too large (max 20 MB)")
        tmp.write(content)
        path = tmp.name
    try:
        preview = entity_import.preview(path, entity_type)
    except ValueError as e:
        Path(path).unlink(missing_ok=True)
        raise HTTPException(400, str(e))
    except Exception as e:
        Path(path).unlink(missing_ok=True)
        raise HTTPException(400, f"Failed to read file: {e}")

    _prune_import_stash()
    session_id = _uuid.uuid4().hex
    _ENTITY_IMPORT_STASH[session_id] = (path, time.time() + _ENTITY_IMPORT_TTL)
    preview["session_id"] = session_id
    return preview


@app.post("/api/entity-import/commit")
def entity_import_commit(body: dict, ctx: dict = Depends(get_current_context)):
    """Finalize the import with the user's chosen column mapping."""
    from api import entity_import
    session_id = body.get("session_id") or ""
    entity_type = body.get("entity_type") or ""
    mapping = body.get("mapping") or {}

    _prune_import_stash()
    entry = _ENTITY_IMPORT_STASH.get(session_id)
    if not entry:
        raise HTTPException(400, "Upload session expired — re-upload the file")
    path, _ = entry

    try:
        result = entity_import.commit(
            ctx["business_id"], ctx["user"]["id"], path, entity_type, mapping,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        # One-shot — file is dropped after commit regardless of outcome.
        Path(path).unlink(missing_ok=True)
        _ENTITY_IMPORT_STASH.pop(session_id, None)
    return result


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
@app.post("/api/voice/memo-to-task")
async def voice_memo_to_task(
    file: UploadFile = File(...),
    language: str = Query("en"),
    ctx: dict = Depends(get_current_context),
):
    """
    Quick voice-memo shortcut: transcribe an audio blob and create a task
    directly from it. The first sentence becomes the title, the rest becomes
    the description. Returns the created task + transcript.
    """
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

        text = (_transcribe(wav_path, language=language) or "").strip()
        if not text:
            raise HTTPException(400, "Could not transcribe audio — try recording again")

        # First sentence → title, rest → description
        parts = text.split(". ", 1)
        title = parts[0][:200].rstrip(".")
        description = (parts[1] if len(parts) > 1 else "").strip()[:4000]

        from api import tasks as _tasks
        task = _tasks.create_task(
            ctx["business_id"], ctx["user"]["id"],
            {"title": title, "description": description, "priority": "normal"},
        )
        return {"task": task, "transcript": text}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if wav_check != tmp_path:
            Path(wav_check).unlink(missing_ok=True)


@app.post("/api/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = Query("en"),
    ctx: dict = Depends(get_current_context),
):
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

        text = _transcribe(wav_path, language=language)
        return {"text": text or "", "success": bool(text), "language": language}
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
from utils.timez import now_utc_naive


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
