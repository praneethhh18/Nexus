"""
Privacy / cloud-LLM audit endpoints. The audit log proves that no raw
prompts left the machine — only SHA-256 hashes plus call metadata. Useful
for compliance reviews and for the in-chat trust UI badge.
"""
from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context, get_current_user

router = APIRouter(tags=["privacy"])


@router.get("/api/privacy/status")
def privacy_status(user: dict = Depends(get_current_user)):
    """
    Summarize the privacy posture: which provider is live, whether the cloud
    kill-switch is on, redaction on, audit logging on, and where the audit
    log lives. Any logged-in user can view; no raw data is exposed.
    """
    from config import privacy
    from config.llm_provider import get_provider, USE_CLAUDE, USE_BEDROCK, CLAUDE_MODEL

    cloud_model = None
    if USE_CLAUDE:
        cloud_model = CLAUDE_MODEL
    elif USE_BEDROCK:
        try:
            from config.llm_bedrock import primary_model_id
            cloud_model = primary_model_id()
        except Exception:
            cloud_model = "bedrock"

    return {
        "provider": get_provider(),
        "cloud_configured": bool(USE_CLAUDE or USE_BEDROCK),
        "cloud_model": cloud_model,
        "allow_cloud_llm": privacy.ALLOW_CLOUD_LLM,
        "redact_pii": privacy.REDACT_PII,
        "audit_enabled": privacy.AUDIT_CLOUD_CALLS,
        "audit_log_path": str(privacy._AUDIT_PATH),
    }


@router.get("/api/privacy/audit")
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


@router.post("/api/privacy/audit/clear")
def privacy_audit_clear(ctx: dict = Depends(get_current_context)):
    """Truncate the cloud audit log. Admin/owner only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can clear the cloud audit log")
    from config import privacy
    if privacy._AUDIT_PATH.exists():
        privacy._AUDIT_PATH.unlink()
    return {"ok": True}


@router.get("/api/privacy/usage")
def privacy_usage_today(ctx: dict = Depends(get_current_context)):
    """
    Today's cloud-LLM token usage and estimated spend for the current business.

    Numbers come from the per-call `nexus_cloud_usage` table written after
    every cloud invocation. The cap is the daily token ceiling — when hit,
    cloud-eligible calls automatically fall back to local Ollama (same effect
    as the kill switch, but only for the day, only for this business).
    """
    from config import cloud_budget
    return cloud_budget.get_today_usage(ctx["business_id"])
