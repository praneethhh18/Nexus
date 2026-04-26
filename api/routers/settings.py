"""
Settings endpoints — read-only system state, runtime cache resets, and
admin-only env-var updates that persist to .env.
"""
from __future__ import annotations

import os
import sys as _sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context, get_current_user

router = APIRouter(tags=["settings"])

ROOT = Path(__file__).parent.parent.parent


@router.get("/api/settings")
def get_settings(ctx: dict = Depends(get_current_context)):
    from config.settings import (
        OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL, EMBED_MODEL,
        EMAIL_ENABLED, DISCORD_ENABLED, MAX_SQL_RETRIES, MAX_REFLECTION_RETRIES,
        CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RETRIEVAL, VERSION,
    )

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


@router.post("/api/settings/reset-llm")
def reset_llm(ctx: dict = Depends(get_current_context)):
    from config.llm_config import reset_instances
    reset_instances()
    return {"ok": True, "message": "LLM connection reset"}


@router.post("/api/settings/clear-cache")
def clear_cache(ctx: dict = Depends(get_current_context)):
    from sql_agent.query_generator import clear_cache as cc
    cc()
    return {"ok": True, "message": "SQL cache cleared"}


@router.post("/api/settings/update")
def update_runtime_setting(body: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")

    key = body.get("key", "")
    value = body.get("value", "")
    allowed = {"DISCORD_WEBHOOK_URL", "SLACK_WEBHOOK_URL", "GMAIL_USER",
               "GMAIL_APP_PASSWORD", "LOG_LEVEL", "ANOMALY_THRESHOLD"}

    if key not in allowed:
        raise HTTPException(
            400, f"Cannot update '{key}'. Allowed: {', '.join(sorted(allowed))}",
        )

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
    os.environ[key] = value
    return {"ok": True, "key": key}
