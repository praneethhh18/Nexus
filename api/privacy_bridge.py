"""Privacy Bridge — per-business Ollama endpoint registration.

The product story:
    NexusAgent SaaS runs on our cloud, but a paying "Privacy" tier customer
    can route their sensitive prompts to an Ollama instance running on
    their OWN laptop. Their data never reaches our LLM provider — it's
    actually computed locally in their machine.

Lifecycle:
    1. Customer installs the Privacy Bridge installer on their laptop.
       The installer pulls Ollama, downloads Llama 3.1 8B, starts a
       Cloudflare Tunnel → exposes localhost:11434 publicly with HTTPS.
    2. Installer POSTs the tunnel URL + an auth token to
       /api/privacy-bridge/register on the SaaS backend.
    3. Backend stores it against their business_id.
    4. Health check loop pings the endpoint every 5 min.
    5. When agent_loop runs a sensitive=True prompt for that business,
       config/llm_provider.py routes it to the customer's endpoint
       instead of cloud LLM. If the endpoint is down → falls back to
       cloud with PII redaction (already-built privacy layer).

Honest threat model:
    - Customer's tunnel URL is essentially a secret. We store it as such.
    - Bridge installer authenticates with a per-business token (issued
      from the Settings page). Token can be revoked — kills the
      registered endpoint.
    - Health-check pings verify reachability + that it's actually Ollama
      (not a generic HTTPS server).
"""
from __future__ import annotations

import json
import re
import secrets
import sqlite3  # sqlite3.Row sentinel
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from loguru import logger

from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_privacy_bridges"


# Status enum:
#   "unconfigured"  — no endpoint registered for this business
#   "registered"    — endpoint registered, never pinged
#   "healthy"       — last ping succeeded
#   "down"          — last ping failed
#   "revoked"       — owner manually disabled, won't auto-route
VALID_STATUSES = ("unconfigured", "registered", "healthy", "down", "revoked")


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            business_id      TEXT PRIMARY KEY,
            endpoint_url     TEXT,
            token            TEXT,           -- shared secret bridge uses to register
            status           TEXT NOT NULL DEFAULT 'unconfigured',
            last_pinged_at   TEXT,
            last_ping_error  TEXT,
            registered_at    TEXT,
            registered_by    TEXT,           -- user_id of whoever turned this on
            ollama_version   TEXT,
            ollama_models    TEXT,           -- JSON list of model names
            updated_at       TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _row_to_dict(row) -> Dict[str, Any]:
    d = dict(row)
    if d.get("ollama_models"):
        try:
            d["ollama_models"] = json.loads(d["ollama_models"])
        except Exception:
            d["ollama_models"] = []
    else:
        d["ollama_models"] = []
    # Never leak the registration token in API responses
    d.pop("token", None)
    return d


# ── Bridge token issuance ──────────────────────────────────────────────────
def issue_token(business_id: str, user_id: str) -> str:
    """Mint a fresh registration token for this business. The Bridge
    installer uses this token to POST its tunnel URL.
    Issuing a new token revokes any previous one (security: lost-laptop case)."""
    token = "pb_" + secrets.token_urlsafe(32)
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {TABLE} (business_id, token, status, registered_by, updated_at) "
            f"VALUES (?, ?, 'unconfigured', ?, ?) "
            f"ON CONFLICT(business_id) DO UPDATE SET "
            f"  token = excluded.token, "
            f"  status = 'unconfigured', "
            f"  endpoint_url = NULL, "
            f"  registered_at = NULL, "
            f"  registered_by = excluded.registered_by, "
            f"  updated_at = excluded.updated_at",
            (business_id, token, user_id, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    return token


def get_state(business_id: str) -> Dict[str, Any]:
    """Read the current bridge state for a business. Always returns a dict
    even if no row exists (status='unconfigured')."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {
            "business_id": business_id,
            "status": "unconfigured",
            "endpoint_url": None,
            "ollama_models": [],
        }
    return _row_to_dict(row)


def get_endpoint_for_use(business_id: str) -> Optional[str]:
    """Return the endpoint URL ONLY if it's currently usable.
    Used by the LLM router. Skips revoked + unconfigured. Returns None if down,
    so the router falls back to cloud-with-redaction immediately."""
    info = get_endpoint_info(business_id)
    return info["endpoint_url"] if info else None


def get_endpoint_info(business_id: str) -> Optional[Dict[str, Any]]:
    """Like get_endpoint_for_use but also returns the registered model list.
    Used by invoke_via_bridge so we don't hardcode a model name the
    customer's Ollama might not have installed."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT endpoint_url, status, ollama_models FROM {TABLE} "
            f"WHERE business_id = ? AND endpoint_url IS NOT NULL",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or row["status"] in ("revoked", "down"):
        return None
    models: list = []
    if row["ollama_models"]:
        try:
            models = json.loads(row["ollama_models"])
        except Exception:
            models = []
    return {"endpoint_url": row["endpoint_url"], "ollama_models": models}


# Models we prefer, in order — first one the customer has installed wins.
# All three are sensible "general purpose" picks the installer recommends.
_PREFERRED_MODELS = (
    "llama3.1:8b-instruct-q4_K_M",
    "llama3.1:8b",
    "llama3:8b",
    "mistral:7b",
    "qwen2.5:7b",
)


def _pick_model(installed: list, override: Optional[str] = None) -> str:
    """Pick the best available model. Prefers explicit override, then our
    preference list, then whatever the customer happens to have installed."""
    if override and any(m == override or m.startswith(override + ":") for m in installed):
        return override
    for pref in _PREFERRED_MODELS:
        if pref in installed:
            return pref
        # Tolerate variant tags ("llama3.1:8b" matches "llama3.1:8b-instruct-...")
        base = pref.split(":")[0]
        for m in installed:
            if m == pref or m.startswith(base + ":"):
                return m
    # Fall back to whatever they have, or the canonical default if list is empty
    return installed[0] if installed else "llama3.1:8b"


# ── Bridge installer registers its tunnel URL here ─────────────────────────
def register_endpoint(*, token: str, endpoint_url: str,
                      ollama_version: str = "",
                      ollama_models: Optional[list] = None) -> Dict[str, Any]:
    """Called by the Privacy Bridge installer after it has Ollama running
    + a Cloudflare Tunnel up. Validates the token, stores the URL, runs
    one immediate health check.

    Raises ValueError on bad token or malformed URL.
    """
    if not token or not token.startswith("pb_"):
        raise ValueError("invalid token format")
    if not endpoint_url or not endpoint_url.startswith("https://"):
        raise ValueError("endpoint_url must be an https:// URL")
    if not _looks_like_ollama_url(endpoint_url):
        raise ValueError("endpoint_url must point to an Ollama server")

    # Look up which business this token belongs to
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT business_id FROM {TABLE} WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise ValueError("token not recognised — issue a new one from Settings")

    business_id = row["business_id"]

    # Health-check the endpoint right now to seed the status
    health = _ping(endpoint_url)
    status = "healthy" if health.get("ok") else "down"

    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET endpoint_url = ?, status = ?, "
            f"last_pinged_at = ?, last_ping_error = ?, registered_at = ?, "
            f"ollama_version = ?, ollama_models = ?, updated_at = ? "
            f"WHERE business_id = ?",
            (endpoint_url, status, now_iso(), health.get("error", ""),
             now_iso(), ollama_version, json.dumps(ollama_models or []),
             now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(
        f"[privacy_bridge] registered {business_id} → {endpoint_url} "
        f"status={status}"
    )
    return {
        "ok":           True,
        "business_id":  business_id,
        "status":       status,
        "ollama_models": ollama_models or [],
        "ping_error":   health.get("error", ""),
    }


def revoke(business_id: str) -> Dict[str, Any]:
    """Owner manually turns off the bridge. Endpoint stays in DB for
    forensic audit but won't be used until they re-register."""
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET status = 'revoked', updated_at = ? "
            f"WHERE business_id = ?",
            (now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_state(business_id)


# ── Health check (runs on a schedule + on every register) ──────────────────
def _looks_like_ollama_url(url: str) -> bool:
    """Cheap sanity check before we hit it — block obvious junk."""
    return bool(re.match(r"^https://[a-zA-Z0-9.-]+(?::\d+)?(?:/.*)?$", url))


def _ping(endpoint_url: str) -> Dict[str, Any]:
    """Hit Ollama's /api/tags to confirm it's actually Ollama and not a
    random HTTPS server pointed at the URL."""
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(endpoint_url.rstrip("/") + "/api/tags")
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:120]}"}
        data = r.json()
        if "models" not in data:
            return {"ok": False, "error": "response doesn't look like Ollama (/api/tags missing 'models')"}
        return {
            "ok":     True,
            "models": [m.get("name", "") for m in data.get("models", [])],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def health_check_one(business_id: str) -> Dict[str, Any]:
    """Re-ping the registered endpoint for one business. Updates status."""
    state = get_state(business_id)
    if state.get("status") == "unconfigured" or not state.get("endpoint_url"):
        return state
    if state.get("status") == "revoked":
        return state  # don't ping revoked endpoints

    health = _ping(state["endpoint_url"])
    new_status = "healthy" if health["ok"] else "down"

    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET status = ?, last_pinged_at = ?, "
            f"last_ping_error = ?, ollama_models = ?, updated_at = ? "
            f"WHERE business_id = ?",
            (new_status, now_iso(), health.get("error", ""),
             json.dumps(health.get("models", [])) if health["ok"] else state.get("ollama_models") and json.dumps(state["ollama_models"]) or "[]",
             now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_state(business_id)


def health_check_all_due(stale_minutes: int = 5) -> int:
    """Re-ping every registered bridge that hasn't been checked in
    `stale_minutes`. Returns count of bridges checked."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)).isoformat()
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT business_id FROM {TABLE} "
            f"WHERE endpoint_url IS NOT NULL AND status != 'revoked' "
            f"AND (last_pinged_at IS NULL OR last_pinged_at < ?)",
            (cutoff,),
        ).fetchall()
    finally:
        conn.close()
    count = 0
    for row in rows:
        try:
            health_check_one(row["business_id"])
            count += 1
        except Exception as e:
            logger.warning(f"[privacy_bridge] health check failed for {row['business_id']}: {e}")
    return count


# ── Forwarder — used by config/llm_provider.py ─────────────────────────────
def invoke_via_bridge(business_id: str, prompt: str, system: str = "",
                      model: Optional[str] = None,
                      max_tokens: int = 1024,
                      temperature: float = 0.4) -> str:
    """Forward an LLM request to the customer's Ollama. Raises RuntimeError
    if endpoint isn't usable (caller falls back to cloud-with-redaction).

    Picks a model from the customer's registered installed-models list so we
    don't hardcode a tag they don't have. Pass `model` to override.
    """
    info = get_endpoint_info(business_id)
    if not info:
        raise RuntimeError("no usable privacy bridge for this business")

    chosen_model = _pick_model(info["ollama_models"], override=model)
    payload = {
        "model": chosen_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(info["endpoint_url"].rstrip("/") + "/api/generate", json=payload)
    except Exception as e:
        # Mark as down so subsequent calls skip it without retrying
        _mark_down(business_id, str(e)[:200])
        raise RuntimeError(f"bridge unreachable: {e}")

    if r.status_code != 200:
        _mark_down(business_id, f"HTTP {r.status_code}")
        raise RuntimeError(f"bridge returned HTTP {r.status_code}")

    return (r.json().get("response") or "").strip()


def stream_via_bridge(business_id: str, prompt: str, system: str = "",
                      model: Optional[str] = None,
                      max_tokens: int = 1024,
                      temperature: float = 0.4):
    """Streaming counterpart to invoke_via_bridge. Yields response chunks as
    they arrive from the customer's Ollama. Raises RuntimeError on failure
    so the caller can fall back to cloud-with-redaction."""
    info = get_endpoint_info(business_id)
    if not info:
        raise RuntimeError("no usable privacy bridge for this business")

    chosen_model = _pick_model(info["ollama_models"], override=model)
    payload = {
        "model": chosen_model,
        "prompt": prompt,
        "system": system,
        "stream": True,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    try:
        with httpx.stream(
            "POST",
            info["endpoint_url"].rstrip("/") + "/api/generate",
            json=payload,
            timeout=120.0,
        ) as r:
            if r.status_code != 200:
                _mark_down(business_id, f"HTTP {r.status_code}")
                raise RuntimeError(f"bridge returned HTTP {r.status_code}")
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except Exception:
                    continue
                piece = chunk.get("response") or ""
                if piece:
                    yield piece
                if chunk.get("done"):
                    break
    except RuntimeError:
        raise
    except Exception as e:
        _mark_down(business_id, str(e)[:200])
        raise RuntimeError(f"bridge unreachable: {e}")


def _mark_down(business_id: str, error: str) -> None:
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET status = 'down', last_pinged_at = ?, "
            f"last_ping_error = ?, updated_at = ? WHERE business_id = ?",
            (now_iso(), error[:200], now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()
