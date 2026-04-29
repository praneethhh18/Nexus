"""
Analytics & forecasting.

Four reports, all strictly scoped by business_id:

  1. pipeline_velocity      — avg days in each stage + stage→won conversion rate
  2. revenue_forecast       — weighted pipeline grouped by expected_close month
  3. agent_impact           — tools run, approvals processed, audit summary
  4. churn_risk             — LLM-assisted risk score per top-value open deal

Everything is computed on the fly from existing tables — no ETL, no cache.
Calls are cheap because SQLite + indexed columns.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

from loguru import logger

from config.settings import DB_PATH
from utils.timez import now_utc_naive
from api.crm import (
    DEALS_TABLE, INTERACTIONS_TABLE,
    DEAL_STAGE_EVENTS_TABLE, DEAL_STAGES,
)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE VELOCITY
# ═══════════════════════════════════════════════════════════════════════════════
def pipeline_velocity(business_id: str) -> Dict[str, Any]:
    """
    Average days spent in each stage, and win rate from each stage.

    Days-in-stage is computed from consecutive stage events: when a deal leaves
    a stage, the time since it entered that stage is the duration. Deals still
    in-stage count up to "now" so we don't understate current velocity.
    """
    conn = _conn()
    try:
        events = conn.execute(
            f"SELECT deal_id, from_stage, to_stage, at FROM {DEAL_STAGE_EVENTS_TABLE} "
            f"WHERE business_id = ? ORDER BY deal_id, at ASC",
            (business_id,),
        ).fetchall()
        deals = conn.execute(
            f"SELECT id, stage, updated_at FROM {DEALS_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()

    # Group events by deal
    per_deal: Dict[str, List[sqlite3.Row]] = {}
    for e in events:
        per_deal.setdefault(e["deal_id"], []).append(e)

    durations: Dict[str, List[float]] = {s: [] for s in DEAL_STAGES}
    # conversions: for each non-terminal stage, how many reached 'won' at all?
    entered_stage: Dict[str, int] = {s: 0 for s in DEAL_STAGES}
    won_after_stage: Dict[str, int] = {s: 0 for s in DEAL_STAGES}

    now = now_utc_naive()
    for deal_id, ev_list in per_deal.items():
        seen_stages: set = set()
        reached_won = any(e["to_stage"] == "won" for e in ev_list)
        for i, e in enumerate(ev_list):
            to_s = e["to_stage"]
            if to_s in entered_stage:
                if to_s not in seen_stages:
                    entered_stage[to_s] += 1
                    if reached_won:
                        won_after_stage[to_s] += 1
                    seen_stages.add(to_s)

            try:
                start = datetime.fromisoformat(e["at"])
            except Exception:
                continue
            if i + 1 < len(ev_list):
                try:
                    end = datetime.fromisoformat(ev_list[i + 1]["at"])
                except Exception:
                    continue
            else:
                # Last known stage — count up to now if still in-flight
                end = now
            days = max(0.0, (end - start).total_seconds() / 86400.0)
            if to_s in durations:
                durations[to_s].append(days)

    by_stage = {}
    for s in DEAL_STAGES:
        ds = durations[s]
        by_stage[s] = {
            "avg_days": round(sum(ds) / len(ds), 1) if ds else None,
            "sample_size": len(ds),
            "entered_count": entered_stage[s],
            "win_rate_pct": round((won_after_stage[s] / entered_stage[s]) * 100, 1)
                            if entered_stage[s] else None,
        }

    # Overall lead→won conversion (uses any deal that entered 'lead')
    leads_total = entered_stage.get("lead", 0)
    leads_won = won_after_stage.get("lead", 0)
    overall_win_rate = round((leads_won / leads_total) * 100, 1) if leads_total else None

    return {
        "by_stage": by_stage,
        "overall_win_rate_pct": overall_win_rate,
        "total_deals_tracked": len(per_deal),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  REVENUE FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
def revenue_forecast(business_id: str, horizon_months: int = 6) -> Dict[str, Any]:
    """
    Weighted pipeline forecast: for each deal in a non-terminal stage with an
    expected_close date, group by month and sum value * probability_pct / 100.

    Unweighted and weighted totals are both reported so the user can see how
    aggressive the probability estimates are.
    """
    conn = _conn()
    try:
        rows = conn.execute(
            f"SELECT id, name, stage, value, currency, probability_pct, expected_close "
            f"FROM {DEALS_TABLE} "
            f"WHERE business_id = ? AND stage NOT IN ('won','lost') "
            f"AND expected_close IS NOT NULL AND expected_close != ''",
            (business_id,),
        ).fetchall()

        # Historical won total this period — for comparison
        last_90 = (now_utc_naive() - timedelta(days=90)).isoformat()
        won_row = conn.execute(
            f"SELECT COUNT(*), COALESCE(SUM(value), 0) FROM {DEALS_TABLE} "
            f"WHERE business_id = ? AND stage = 'won' AND updated_at >= ?",
            (business_id, last_90),
        ).fetchone()
    finally:
        conn.close()

    today = date.today()
    horizon_end = date(today.year + (today.month + horizon_months - 1) // 12,
                       ((today.month + horizon_months - 1) % 12) + 1, 1)

    months: Dict[str, Dict[str, float]] = {}
    deals_in_window: List[Dict[str, Any]] = []
    currency_hint = None

    for r in rows:
        try:
            close = date.fromisoformat((r["expected_close"] or "")[:10])
        except Exception:
            continue
        if close < today or close >= horizon_end:
            continue
        currency_hint = currency_hint or r["currency"] or "USD"
        key = close.strftime("%Y-%m")
        bucket = months.setdefault(key, {"month": key, "weighted": 0.0, "unweighted": 0.0, "deal_count": 0})
        value = float(r["value"] or 0)
        prob = max(0, min(100, int(r["probability_pct"] or 0)))
        bucket["weighted"] += value * (prob / 100.0)
        bucket["unweighted"] += value
        bucket["deal_count"] += 1

        deals_in_window.append({
            "id": r["id"], "name": r["name"], "stage": r["stage"],
            "value": value, "currency": r["currency"],
            "probability_pct": prob, "expected_close": r["expected_close"][:10],
            "weighted_value": round(value * prob / 100.0, 2),
        })

    # Fill empty months in range for a smooth chart
    cursor = date(today.year, today.month, 1)
    full_months: List[Dict[str, Any]] = []
    while cursor < horizon_end:
        key = cursor.strftime("%Y-%m")
        m = months.get(key, {"month": key, "weighted": 0.0, "unweighted": 0.0, "deal_count": 0})
        m["weighted"] = round(m["weighted"], 2)
        m["unweighted"] = round(m["unweighted"], 2)
        full_months.append(m)
        cursor = date(cursor.year + (cursor.month // 12), (cursor.month % 12) + 1, 1)

    return {
        "currency": currency_hint or "USD",
        "months": full_months,
        "totals": {
            "weighted": round(sum(m["weighted"] for m in full_months), 2),
            "unweighted": round(sum(m["unweighted"] for m in full_months), 2),
            "deal_count": sum(m["deal_count"] for m in full_months),
        },
        "last_90_won": {
            "deal_count": won_row[0] if won_row else 0,
            "total_value": float((won_row[1] if won_row else 0) or 0),
        },
        "deals": sorted(deals_in_window, key=lambda d: d["expected_close"]),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT IMPACT
# ═══════════════════════════════════════════════════════════════════════════════
def agent_impact(business_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Summary of what the agent has been doing for this business.

      - tool_calls_by_name: counts per agent.X tool in the window
      - approvals: pending/executed/rejected counts
      - total_tool_calls, success_rate, avg_duration_ms
      - estimated_minutes_saved: crude heuristic (each tool call ~= 3 minutes
        of manual work, overrideable).
    """
    cutoff = (now_utc_naive() - timedelta(days=days)).isoformat()
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT tool_name, COUNT(*) AS cnt, AVG(duration_ms) AS avg_d, AVG(success) AS rate "
            "FROM nexus_audit_log WHERE business_id = ? AND timestamp >= ? AND tool_name LIKE 'agent.%' "
            "GROUP BY tool_name ORDER BY cnt DESC",
            (business_id, cutoff),
        ).fetchall()
        total_row = conn.execute(
            "SELECT COUNT(*), AVG(duration_ms), AVG(success) FROM nexus_audit_log "
            "WHERE business_id = ? AND timestamp >= ?",
            (business_id, cutoff),
        ).fetchone()
        approvals_rows = conn.execute(
            "SELECT status, COUNT(*) FROM nexus_agent_approvals "
            "WHERE business_id = ? AND created_at >= ? GROUP BY status",
            (business_id, cutoff),
        ).fetchall()
    finally:
        conn.close()

    by_tool = [
        {
            "tool": r["tool_name"].replace("agent.", ""),
            "count": r["cnt"],
            "avg_duration_ms": round(r["avg_d"] or 0, 1),
            "success_rate_pct": round((r["rate"] or 0) * 100, 1),
        }
        for r in rows
    ]
    approvals = {r[0]: r[1] for r in approvals_rows}
    total_calls = int(total_row[0] or 0)
    avg_duration = round((total_row[1] or 0), 1)
    success_rate = round((total_row[2] or 0) * 100, 1)

    # Minutes saved heuristic — tunable. Tools that require approval (deletions,
    # emails) only count if they were actually executed.
    minutes_saved = 0
    for r in by_tool:
        weight = 5 if r["tool"].startswith(("send_", "generate_", "create_invoice")) else 3
        minutes_saved += r["count"] * weight

    return {
        "window_days": days,
        "total_tool_calls": total_calls,
        "avg_duration_ms": avg_duration,
        "success_rate_pct": success_rate,
        "by_tool": by_tool,
        "approvals": {
            "pending": int(approvals.get("pending", 0)),
            "executed": int(approvals.get("executed", 0)),
            "rejected": int(approvals.get("rejected", 0)),
            "expired": int(approvals.get("expired", 0)),
            "failed": int(approvals.get("failed", 0)),
        },
        "estimated_minutes_saved": minutes_saved,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CHURN RISK
# ═══════════════════════════════════════════════════════════════════════════════
def churn_risk(business_id: str, max_deals: int = 15) -> Dict[str, Any]:
    """
    Score the top open deals by risk of stalling, using a deterministic heuristic
    with an optional LLM-generated suggested action.

    Risk factors:
      - days since last interaction on this deal/contact (or since creation)
      - days in current stage (relative to stage's median)
      - missed expected_close
      - zero interactions logged despite being > 7 days old
    """
    conn = _conn()
    try:
        deals = conn.execute(
            f"SELECT d.id, d.name, d.stage, d.value, d.currency, d.probability_pct, "
            f"d.contact_id, d.company_id, d.expected_close, d.created_at, d.updated_at "
            f"FROM {DEALS_TABLE} d "
            f"WHERE d.business_id = ? AND d.stage NOT IN ('won','lost') "
            f"ORDER BY d.value DESC LIMIT ?",
            (business_id, max_deals * 2),  # fetch extra so we can filter
        ).fetchall()
    finally:
        conn.close()

    now = now_utc_naive()
    today = date.today()

    scored: List[Dict[str, Any]] = []
    conn = _conn()
    try:
        for d in deals:
            factors: List[str] = []
            score = 0

            # Days since last interaction on this deal or its contact
            last_interaction = conn.execute(
                f"SELECT MAX(occurred_at) FROM {INTERACTIONS_TABLE} "
                f"WHERE business_id = ? AND (deal_id = ? OR contact_id = ?)",
                (business_id, d["id"], d["contact_id"]),
            ).fetchone()[0]
            last_touch = last_interaction or d["updated_at"]
            try:
                last_dt = datetime.fromisoformat(last_touch)
                silence_days = (now - last_dt).days
            except Exception:
                silence_days = 0
            if silence_days > 21:
                score += 35
                factors.append(f"silent for {silence_days} days")
            elif silence_days > 10:
                score += 15
                factors.append(f"{silence_days} days since last touch")

            # Missed expected_close
            if d["expected_close"]:
                try:
                    close = date.fromisoformat(d["expected_close"][:10])
                    if close < today:
                        overdue_days = (today - close).days
                        score += min(30, 10 + overdue_days)
                        factors.append(f"close date passed {overdue_days} days ago")
                except Exception:
                    pass

            # Time in current stage (approximated by updated_at)
            try:
                updated_dt = datetime.fromisoformat(d["updated_at"])
                stage_days = (now - updated_dt).days
            except Exception:
                stage_days = 0
            if d["stage"] in ("proposal", "negotiation") and stage_days > 14:
                score += 20
                factors.append(f"{stage_days} days in {d['stage']}")
            elif d["stage"] in ("lead", "qualified") and stage_days > 30:
                score += 15
                factors.append(f"stuck in {d['stage']} for {stage_days} days")

            # Low probability + high value → notable
            if (d["probability_pct"] or 0) < 30 and (d["value"] or 0) > 5000:
                score += 10
                factors.append("low confidence on a high-value deal")

            score = min(100, score)
            scored.append({
                "deal_id": d["id"],
                "name": d["name"],
                "stage": d["stage"],
                "value": float(d["value"] or 0),
                "currency": d["currency"] or "USD",
                "probability_pct": d["probability_pct"],
                "silence_days": silence_days,
                "risk_score": score,
                "risk_level": "high" if score >= 50 else "medium" if score >= 25 else "low",
                "factors": factors,
            })
    finally:
        conn.close()

    scored.sort(key=lambda x: x["risk_score"], reverse=True)
    scored = scored[:max_deals]

    # Ask the LLM for a 1-line action suggestion on each high-risk deal.
    # Skip if there are none — don't burn tokens for nothing.
    high = [s for s in scored if s["risk_score"] >= 50]
    if high:
        from config.llm_provider import invoke as llm_invoke
        try:
            bullets = "\n".join(
                f"- {s['name']} ({s['stage']}, {s['currency']} {int(s['value'])}, "
                f"score {s['risk_score']}): {', '.join(s['factors']) or 'no clear factors'}"
                for s in high
            )
            prompt = (
                "For each deal below, suggest ONE short actionable next step "
                "(max 12 words). Return ONLY a JSON object mapping deal name → "
                "action string. No markdown.\n\n" + bullets
            )
            raw = llm_invoke(prompt, system="You are a pragmatic sales coach.",
                             max_tokens=400, temperature=0.2)
            import json
            import re
            stripped = raw.strip()
            if stripped.startswith("```"):
                stripped = re.sub(r"^```(?:json)?|```$", "", stripped, flags=re.MULTILINE).strip()
            try:
                actions = json.loads(stripped)
            except Exception:
                m = re.search(r"\{[\s\S]*\}", stripped)
                actions = json.loads(m.group(0)) if m else {}
            for s in scored:
                if s["name"] in actions:
                    s["suggested_action"] = str(actions[s["name"]])[:140]
        except Exception as e:
            logger.debug(f"[Analytics] LLM churn suggestions failed: {e}")

    return {
        "total_high": sum(1 for s in scored if s["risk_level"] == "high"),
        "total_medium": sum(1 for s in scored if s["risk_level"] == "medium"),
        "deals": scored,
    }
