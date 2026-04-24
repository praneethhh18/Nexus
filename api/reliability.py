"""
Reliability layer — rate limiting, deep health checks, request-timeout helpers.

Rate limiter: pure-Python token-bucket keyed by (client-ip, route-bucket),
trimmed to keep the memory footprint bounded on a long-running process.
No Redis, no external service — the local-first product runs on a laptop.

Deep health: aggregates DB connectivity, scheduler job count, Ollama reach,
and disk-space checks into one blob for monitoring dashboards.

Request timeout: small `with_timeout(coro, seconds)` helper used in hot paths
so a stuck LLM call doesn't wedge an endpoint forever.
"""
from __future__ import annotations

import asyncio
import os
import sqlite3
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Tuple

from fastapi import HTTPException, Request
from loguru import logger

from config.settings import DB_PATH


# ── Rate limiter ────────────────────────────────────────────────────────────
# Each bucket is a deque of recent request timestamps. We drop anything older
# than `window_seconds` on every hit and compare len(deque) to `max_requests`.
# O(k) per call where k ≈ max_requests — fast enough for the volumes this
# product sees. Buckets auto-evict when untouched for 10 × window.
_WINDOW_SEC = 60
_DEFAULT_LIMIT = 120
_BUCKET_LIMITS: Dict[str, int] = {
    # Specific buckets can override the default. Keys are prefixes on the
    # request path after leading `/api/` is stripped.
    "voice/":    20,
    "voice/memo-to-task": 10,
    "auth/":     30,
    "webhooks/": 300,   # Webhooks can be chatty; downstream signature check gates abuse.
}

_buckets: Dict[str, Deque[float]] = defaultdict(deque)
_last_touch: Dict[str, float] = {}


def _bucket_key(path: str, client: str) -> Tuple[str, int]:
    trimmed = path[len("/api/"):] if path.startswith("/api/") else path
    limit = _DEFAULT_LIMIT
    # Longest-prefix match wins.
    for prefix, n in sorted(_BUCKET_LIMITS.items(), key=lambda x: -len(x[0])):
        if trimmed.startswith(prefix):
            limit = n
            break
    return f"{client}::{trimmed.split('/', 1)[0]}", limit


def _prune() -> None:
    """Drop idle buckets so the dict doesn't grow forever."""
    if len(_buckets) < 2000:
        return
    cutoff = time.time() - (10 * _WINDOW_SEC)
    dead = [k for k, t in _last_touch.items() if t < cutoff]
    for k in dead:
        _buckets.pop(k, None)
        _last_touch.pop(k, None)


async def rate_limit_middleware(request: Request, call_next):
    """
    ASGI middleware. Applied to every /api/* request. Returns 429 once the
    client exceeds their per-route bucket within the window.
    """
    path = request.url.path
    if not path.startswith("/api/"):
        return await call_next(request)
    client = (request.client.host if request.client else "unknown") or "unknown"
    key, limit = _bucket_key(path, client)

    now = time.time()
    dq = _buckets[key]
    cutoff = now - _WINDOW_SEC
    while dq and dq[0] < cutoff:
        dq.popleft()
    if len(dq) >= limit:
        retry_after = max(1, int(_WINDOW_SEC - (now - dq[0])))
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests",
                "retry_after_seconds": retry_after,
                "limit": limit,
                "window_seconds": _WINDOW_SEC,
            },
            headers={"Retry-After": str(retry_after)},
        )
    dq.append(now)
    _last_touch[key] = now
    if len(_buckets) % 500 == 0:
        _prune()

    # Count this call in the usage metrics log. Best-effort; failure here
    # must not block the request.
    try:
        business_id = request.headers.get("x-business-id") or "anonymous"
        from api import usage_metrics
        usage_metrics.record(business_id, "api_call", user_id=client)
    except Exception:
        pass

    return await call_next(request)


def rate_limit_stats() -> Dict[str, Any]:
    """Snapshot for the admin health page."""
    return {
        "buckets_tracked":  len(_buckets),
        "default_limit":    _DEFAULT_LIMIT,
        "window_seconds":   _WINDOW_SEC,
        "overrides":        dict(_BUCKET_LIMITS),
    }


# ── Deep health check ──────────────────────────────────────────────────────
def deep_health() -> Dict[str, Any]:
    """One blob covering every subsystem, suitable for a monitoring dashboard."""
    checks: Dict[str, Any] = {}
    overall_ok = True

    # Database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1").fetchone()
        row = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()
        conn.close()
        checks["database"] = {"ok": True, "tables": int(row[0] or 0)}
    except Exception as e:
        checks["database"] = {"ok": False, "error": str(e)}
        overall_ok = False

    # Provider
    try:
        from config.llm_provider import health_check as ph, get_provider
        result = ph()
        checks["llm"] = {"ok": True, "provider": get_provider(), **result}
    except Exception as e:
        checks["llm"] = {"ok": False, "error": str(e)}
        overall_ok = False

    # Scheduler
    try:
        from agents.background.scheduler import list_jobs
        jobs = list_jobs()
        checks["scheduler"] = {"ok": True, "job_count": len(jobs)}
    except Exception as e:
        checks["scheduler"] = {"ok": False, "error": str(e)}
        # Scheduler failure isn't a total outage — mark degraded, not down.

    # Disk space of the DB volume
    try:
        import shutil
        total, used, free = shutil.disk_usage(str(Path(DB_PATH).parent))
        free_gb = free / (1024 ** 3)
        checks["disk"] = {
            "ok": free_gb > 0.5,   # less than 500MB free is concerning
            "free_gb": round(free_gb, 2),
            "used_pct": round(used / total * 100, 1),
        }
        if not checks["disk"]["ok"]:
            overall_ok = False
    except Exception as e:
        checks["disk"] = {"ok": False, "error": str(e)}

    # Audit log file size (sanity check)
    try:
        audit_path = Path(DB_PATH).parent.parent / "outputs" / "cloud_audit.jsonl"
        if audit_path.exists():
            size_mb = audit_path.stat().st_size / (1024 ** 2)
            checks["audit_log"] = {"ok": True, "size_mb": round(size_mb, 2)}
        else:
            checks["audit_log"] = {"ok": True, "size_mb": 0}
    except Exception as e:
        checks["audit_log"] = {"ok": False, "error": str(e)}

    # Rate limiter snapshot
    checks["rate_limiter"] = {"ok": True, **rate_limit_stats()}

    return {
        "ok": overall_ok,
        "timestamp": time.time(),
        "checks": checks,
    }


# ── Request timeout helper ─────────────────────────────────────────────────
async def with_timeout(coro, seconds: float, label: str = "op"):
    """
    Await a coroutine with a timeout; raises HTTPException 504 on timeout.
    Used in chat / agent / report endpoints where a stuck LLM call would
    otherwise wedge the endpoint indefinitely.
    """
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        logger.warning(f"[Timeout] {label} exceeded {seconds}s")
        raise HTTPException(504, f"{label} timed out after {seconds:.0f}s")
