"""
Usage metrics (11.1) — per-tenant counters rolled up by day.

Drives two things:
  * The product-analytics view at /admin/metrics (DAU/WAU, top agents,
    API volume, per-tenant breakdown)
  * Future usage-based billing in Phase 10 (lives dormant until then)

Storage:
  `nexus_usage_events` is a thin append-only log of interesting events:
      (business_id, user_id, event, day, count).
  A single row per (business, user, event, day) — counter bumped via
  INSERT ... ON CONFLICT. Keeps the total row count bounded: at most
  N_tenants × N_users × N_event_types × N_days.

We *do not* store any payload body / prompt text here — just counters.
That matches the privacy layer's posture: metrics are a count, not a copy.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from config.settings import DB_PATH

TABLE = "nexus_usage_events"

# Known event types. Recording an unknown event is allowed but adapters should
# stick to these constants so the dashboard has stable buckets.
EVENTS = {
    "api_call":         "Any /api/* request",
    "chat_message":     "A message sent in Chat or Agent chat",
    "agent_run":        "A scheduled or manual agent run",
    "tool_call":        "A tool invoked by the agent loop",
    "document_upload":  "A document ingested into RAG",
    "report_generated": "A PDF report generated",
    "workflow_run":     "A workflow executed end-to-end",
}


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            business_id TEXT NOT NULL,
            user_id     TEXT NOT NULL DEFAULT 'system',
            event       TEXT NOT NULL,
            day         TEXT NOT NULL,
            count       INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (business_id, user_id, event, day)
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_biz_day ON {TABLE}(business_id, day)"
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_day_event ON {TABLE}(day, event)"
    )
    conn.commit()
    return conn


def _today() -> str:
    return date.today().isoformat()


# ── Recording ──────────────────────────────────────────────────────────────
def record(business_id: str, event: str, *, user_id: str = "system",
           count: int = 1, day: Optional[str] = None) -> None:
    """
    Bump the counter for (business_id, user_id, event, day). Safe to call from
    anywhere; swallows errors so a logging failure never breaks the request.
    """
    try:
        d = day or _today()
        conn = _conn()
        try:
            conn.execute(
                f"INSERT INTO {TABLE} (business_id, user_id, event, day, count) "
                f"VALUES (?, ?, ?, ?, ?) "
                f"ON CONFLICT(business_id, user_id, event, day) DO UPDATE SET "
                f"count = count + excluded.count",
                (business_id, user_id, event, d, int(count)),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.debug(f"[metrics] record({event}) failed: {e}")


# ── Queries ─────────────────────────────────────────────────────────────────
def totals(business_id: Optional[str] = None, days: int = 30) -> Dict[str, int]:
    """Sum of counters per event type over the last `days` days."""
    cutoff = (date.today() - timedelta(days=max(1, days) - 1)).isoformat()
    conn = _conn()
    try:
        if business_id:
            rows = conn.execute(
                f"SELECT event, SUM(count) FROM {TABLE} "
                f"WHERE business_id = ? AND day >= ? GROUP BY event",
                (business_id, cutoff),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT event, SUM(count) FROM {TABLE} "
                f"WHERE day >= ? GROUP BY event",
                (cutoff,),
            ).fetchall()
    finally:
        conn.close()
    out = {e: 0 for e in EVENTS}
    for event, total in rows:
        out[event] = int(total or 0)
    return out


def series(event: str, days: int = 30,
           business_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Day-by-day time series for one event — powers the dashboard chart."""
    cutoff = (date.today() - timedelta(days=max(1, days) - 1)).isoformat()
    conn = _conn()
    try:
        if business_id:
            rows = conn.execute(
                f"SELECT day, SUM(count) FROM {TABLE} "
                f"WHERE event = ? AND day >= ? AND business_id = ? "
                f"GROUP BY day ORDER BY day",
                (event, cutoff, business_id),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT day, SUM(count) FROM {TABLE} "
                f"WHERE event = ? AND day >= ? GROUP BY day ORDER BY day",
                (event, cutoff),
            ).fetchall()
    finally:
        conn.close()
    by_day = {r[0]: int(r[1] or 0) for r in rows}
    # Fill missing days with 0 so charts render a continuous axis.
    out = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        out.append({"day": d, "count": by_day.get(d, 0)})
    return out


def active_users(days: int = 1, business_id: Optional[str] = None) -> int:
    """DAU (days=1), WAU (days=7), MAU (days=30) based on api_call events."""
    cutoff = (date.today() - timedelta(days=max(1, days) - 1)).isoformat()
    conn = _conn()
    try:
        if business_id:
            row = conn.execute(
                f"SELECT COUNT(DISTINCT user_id) FROM {TABLE} "
                f"WHERE day >= ? AND business_id = ? "
                f"AND event = 'api_call' AND user_id != 'system'",
                (cutoff, business_id),
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT COUNT(DISTINCT user_id) FROM {TABLE} "
                f"WHERE day >= ? AND event = 'api_call' AND user_id != 'system'",
                (cutoff,),
            ).fetchone()
    finally:
        conn.close()
    return int(row[0] or 0) if row else 0


def active_businesses(days: int = 30) -> int:
    """Count tenants that generated any event in the window."""
    cutoff = (date.today() - timedelta(days=max(1, days) - 1)).isoformat()
    conn = _conn()
    try:
        row = conn.execute(
            f"SELECT COUNT(DISTINCT business_id) FROM {TABLE} WHERE day >= ?",
            (cutoff,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0] or 0) if row else 0


def top_tenants(event: str = "api_call", days: int = 30, limit: int = 10
                ) -> List[Dict[str, Any]]:
    """Biggest consumers of a given event — feeds the per-tenant table."""
    cutoff = (date.today() - timedelta(days=max(1, days) - 1)).isoformat()
    conn = _conn()
    try:
        rows = conn.execute(
            f"SELECT business_id, SUM(count) FROM {TABLE} "
            f"WHERE event = ? AND day >= ? "
            f"GROUP BY business_id ORDER BY 2 DESC LIMIT ?",
            (event, cutoff, int(limit)),
        ).fetchall()
    finally:
        conn.close()
    return [{"business_id": r[0], "count": int(r[1] or 0)} for r in rows]


# ── Dashboard snapshot ─────────────────────────────────────────────────────
def dashboard(business_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """
    One blob consumed by the admin metrics page. Includes:
      - Top-line counters over the window
      - DAU / WAU / MAU
      - Active businesses
      - 30-day api_call + agent_run time series
      - Top tenants by api_call
    """
    return {
        "days":      days,
        "scope":     "tenant" if business_id else "global",
        "business_id": business_id,
        "totals":    totals(business_id, days=days),
        "events":    {k: v["description"] if isinstance(v, dict) else v
                      for k, v in [(ek, {"description": ev}) for ek, ev in EVENTS.items()]},
        "dau":       active_users(1,  business_id),
        "wau":       active_users(7,  business_id),
        "mau":       active_users(30, business_id),
        "active_businesses": active_businesses(30),
        "api_series":  series("api_call",  days=days, business_id=business_id),
        "runs_series": series("agent_run", days=days, business_id=business_id),
        "top_tenants": top_tenants(event="api_call", days=days, limit=10)
                       if business_id is None else [],
    }
