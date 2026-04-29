"""
Cloud LLM cost guardrails.

After we opened the cloud path for DB-query explanations and WhatsApp voice
turns, an unbounded agent loop or chatty user could quietly burn through a
Bedrock / Anthropic bill. This module is the spend brake:

    1. **Budget cap per business per day.** Total tokens (input + output)
       are tallied per `business_id` per UTC date in `nexus_cloud_usage`.
       When the cap is exceeded, `should_allow_cloud()` returns False —
       cloud-eligible callers fall back to local Ollama, behaving identically
       to the existing `ALLOW_CLOUD_LLM=false` kill switch.

    2. **Per-call recording.** After each cloud call, the caller records
       `(business_id, tokens_in, tokens_out, model)`. Numbers come from the
       provider response (Anthropic / Bedrock both return usage). Local
       Ollama is free → not tracked.

    3. **Read-only API.** `get_today_usage(business_id)` returns
       {tokens_in, tokens_out, calls, est_cost_usd, cap, over_budget}.
       The Security panel renders this so users see live spend.

The module is *advisory, not transactional* — if a request races past the cap
by a few thousand tokens, that's fine. The cap is a daily ceiling, not a
metering license.

Privacy: this table records counts only. Never prompt text, never user IDs.
"""
from __future__ import annotations

import contextvars
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from config.settings import DB_PATH

USAGE_TABLE = "nexus_cloud_usage"

# Default daily token cap per business. Generous enough that normal use never
# trips it; low enough that a runaway agent loop is caught within minutes.
# Override with CLOUD_TOKEN_DAILY_CAP env var (set to 0 to disable the brake).
DEFAULT_DAILY_CAP = int(os.getenv("CLOUD_TOKEN_DAILY_CAP", "1000000"))

# Rough USD-per-1M-tokens for the est_cost_usd readout. Real billing comes
# from your provider — these are display estimates, not invoices.
_PRICE_PER_MTOK = {
    # Bedrock Nova Pro (text only, on-demand)
    "amazon.nova-pro-v1:0":   {"in": 0.80, "out": 3.20},
    "amazon.nova-lite-v1:0":  {"in": 0.06, "out": 0.24},
    "amazon.nova-micro-v1:0": {"in": 0.035, "out": 0.14},
    # Anthropic Claude (May 2024 pricing)
    "claude-sonnet-4-20250514": {"in": 3.00, "out": 15.00},
    "claude-haiku-4-5-20251001": {"in": 1.00, "out": 5.00},
    "claude-opus-4-7":          {"in": 15.00, "out": 75.00},
}
_DEFAULT_PRICE = {"in": 1.00, "out": 4.00}


# ── Active-business context (set by agent loop, read by cloud callers) ─────
_active_business: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_nexus_active_business", default=None,
)


def set_active_business(business_id: Optional[str]) -> contextvars.Token:
    """
    Mark this async/sync call chain as belonging to `business_id`. Cloud
    invocations downstream check the budget for this business and record
    usage against it. Returns a token; pass it to `reset_active_business`
    to undo.
    """
    return _active_business.set(business_id)


def reset_active_business(token: contextvars.Token) -> None:
    _active_business.reset(token)


def get_active_business() -> Optional[str]:
    return _active_business.get()


# ── Schema ─────────────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {USAGE_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id TEXT NOT NULL,
        date TEXT NOT NULL,            -- UTC YYYY-MM-DD
        ts   TEXT NOT NULL,            -- ISO timestamp of the call
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        tokens_in  INTEGER DEFAULT 0,
        tokens_out INTEGER DEFAULT 0,
        est_cost_usd REAL DEFAULT 0
    )""")
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_cloud_usage_biz_date "
        f"ON {USAGE_TABLE}(business_id, date)"
    )
    conn.commit()
    return conn


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p = _PRICE_PER_MTOK.get(model, _DEFAULT_PRICE)
    return round(
        (tokens_in / 1_000_000.0) * p["in"]
        + (tokens_out / 1_000_000.0) * p["out"],
        6,
    )


# ── Public API ──────────────────────────────────────────────────────────────
def record_usage(
    business_id: Optional[str],
    provider: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
) -> None:
    """Append a usage row. Best-effort: never raises."""
    biz = (business_id or get_active_business() or "_system").strip() or "_system"
    if tokens_in <= 0 and tokens_out <= 0:
        return
    try:
        conn = _conn()
        conn.execute(
            f"INSERT INTO {USAGE_TABLE} "
            f"(business_id, date, ts, provider, model, tokens_in, tokens_out, est_cost_usd) "
            f"VALUES (?,?,?,?,?,?,?,?)",
            (
                biz, _today_utc(),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                provider, model, int(tokens_in), int(tokens_out),
                _estimate_cost_usd(model, tokens_in, tokens_out),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"[cloud_budget] record_usage failed: {e}")


def get_today_usage(business_id: Optional[str] = None) -> Dict[str, Any]:
    """Return today's spend stats for a business (or active context)."""
    biz = (business_id or get_active_business() or "_system").strip() or "_system"
    cap = get_daily_cap()
    try:
        conn = _conn()
        row = conn.execute(
            f"SELECT COALESCE(SUM(tokens_in),0)  AS tin, "
            f"       COALESCE(SUM(tokens_out),0) AS tout, "
            f"       COALESCE(SUM(est_cost_usd),0) AS cost, "
            f"       COUNT(*) AS calls "
            f"FROM {USAGE_TABLE} WHERE business_id = ? AND date = ?",
            (biz, _today_utc()),
        ).fetchone()
        conn.close()
        tin, tout, cost, calls = row
    except Exception as e:
        logger.warning(f"[cloud_budget] get_today_usage failed: {e}")
        tin = tout = calls = 0
        cost = 0.0

    total_tokens = int(tin) + int(tout)
    return {
        "business_id": biz,
        "date": _today_utc(),
        "tokens_in":  int(tin),
        "tokens_out": int(tout),
        "tokens_total": total_tokens,
        "calls": int(calls),
        "est_cost_usd": round(float(cost), 4),
        "cap": cap,
        "over_budget": (cap > 0 and total_tokens >= cap),
    }


def get_daily_cap(business_id: Optional[str] = None) -> int:
    """Per-business cap. v1 reads from env only; future: per-business override
    in a settings table."""
    return DEFAULT_DAILY_CAP


def should_allow_cloud(business_id: Optional[str] = None) -> bool:
    """
    Cheap budget check called before every cloud-eligible LLM call.
    Returns False if today's tokens have hit the cap (forces local fallback).

    A cap of 0 means "no cap" — always returns True.
    """
    cap = get_daily_cap(business_id)
    if cap <= 0:
        return True
    usage = get_today_usage(business_id)
    if usage["over_budget"]:
        logger.warning(
            f"[cloud_budget] business {usage['business_id']} hit daily cap "
            f"({usage['tokens_total']}/{cap} tokens) — forcing local fallback"
        )
        return False
    return True
