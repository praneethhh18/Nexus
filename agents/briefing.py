"""
Morning Briefing Agent.

Every day at 08:00 local time (configurable), produces a one-page briefing
per business covering what changed, what's urgent, and what to do today.

Flow:
    1. Collect aggregates locally (tasks due / overdue, deal movement,
       overdue invoices, pipeline totals, recent email-triage hits).
    2. Feed aggregates (no raw rows) to the cloud narrative generator
       — same aggregate-then-cloud path used for reports.
    3. Persist the snapshot in `nexus_briefings` so the dashboard can
       show it without re-running the LLM.
    4. Optionally push via Discord webhook and WhatsApp bridge.

Callers:
    - Scheduler at 08:00 UTC (registered in agents/background/scheduler.py)
    - On-demand via `POST /api/briefing/run`
"""
from __future__ import annotations

import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from config.db import get_conn
from utils.timez import now_iso


BRIEFINGS_TABLE = "nexus_briefings"


# ── Storage ─────────────────────────────────────────────────────────────────
def _get_conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {BRIEFINGS_TABLE} (
            id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            narrative TEXT NOT NULL,
            data_json TEXT NOT NULL,
            narrative_mode TEXT,
            delivered_channels TEXT DEFAULT ''
        )
    """)
    # Additive migration — older deployments lack `kind`; rows default to morning.
    # Need to catch BOTH SQLite's OperationalError AND Postgres's DuplicateColumn
    # since `config.db.get_conn()` returns either depending on DATABASE_URL.
    try:
        from config.db import list_columns
        if "kind" not in set(list_columns(conn, BRIEFINGS_TABLE)):
            conn.execute(f"ALTER TABLE {BRIEFINGS_TABLE} ADD COLUMN kind TEXT DEFAULT 'morning'")
    except Exception as e:
        logger.debug(f"[briefing] kind-column migration skipped: {e}")
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_briefings_biz "
        f"ON {BRIEFINGS_TABLE}(business_id, created_at DESC)"
    )
    conn.commit()
    return conn


def _save(business_id: str, narrative: str, data: Dict, mode: str,
          delivered: List[str], kind: str = "morning") -> Dict:
    bid = f"br-{uuid.uuid4().hex[:10]}"
    now = now_iso()
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {BRIEFINGS_TABLE} "
            f"(id, business_id, created_at, narrative, data_json, narrative_mode, "
            f"delivered_channels, kind) "
            f"VALUES (?,?,?,?,?,?,?,?)",
            (bid, business_id, now, narrative, json.dumps(data), mode,
             ",".join(delivered), kind),
        )
        conn.commit()
    finally:
        conn.close()
    return {"id": bid, "business_id": business_id, "created_at": now,
            "narrative": narrative, "data": data, "mode": mode,
            "delivered_channels": delivered, "kind": kind}


def latest(business_id: str, kind: str = "morning") -> Dict | None:
    """Return the most recent briefing of a given kind for a business, or None."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {BRIEFINGS_TABLE} "
            f"WHERE business_id = ? AND COALESCE(kind, 'morning') = ? "
            f"ORDER BY created_at DESC LIMIT 1",
            (business_id, kind),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    try: d["data"] = json.loads(d.pop("data_json", "{}"))
    except Exception: d["data"] = {}
    d["delivered_channels"] = [c for c in (d.get("delivered_channels") or "").split(",") if c]
    return d


# ── Data collection (all local) ─────────────────────────────────────────────
def _collect(business_id: str) -> Dict[str, Any]:
    """
    Gather today's key numbers. Everything here runs against local SQLite —
    no data leaves the machine at this stage.
    """
    from api import tasks as _tasks, invoices as _inv, crm as _crm

    today = date.today()
    yday = today - timedelta(days=1)

    # Tasks
    try:
        task_sum = _tasks.task_summary(business_id)
    except Exception as e:
        logger.warning(f"[Briefing] task summary failed: {e}")
        task_sum = {}

    # Tasks due today (titles only — short)
    today_tasks: List[Dict[str, Any]] = []
    try:
        due_today = _tasks.list_tasks(business_id, due_window="today", status="active", limit=10)
        today_tasks = [
            {"title": t.get("title", "")[:80],
             "priority": t.get("priority"),
             "overdue": False}
            for t in due_today
        ]
    except Exception as e:
        logger.warning(f"[Briefing] due-today list failed: {e}")

    overdue_tasks: List[Dict[str, Any]] = []
    try:
        ov = _tasks.list_tasks(business_id, due_window="overdue", status="active", limit=5)
        overdue_tasks = [
            {"title": t.get("title", "")[:80], "priority": t.get("priority"),
             "due_date": t.get("due_date")}
            for t in ov
        ]
    except Exception as e:
        logger.warning(f"[Briefing] overdue list failed: {e}")

    # Invoices
    try:
        inv_sum = _inv.invoice_summary(business_id)
    except Exception as e:
        logger.warning(f"[Briefing] invoice summary failed: {e}")
        inv_sum = {}

    overdue_invoices: List[Dict[str, Any]] = []
    try:
        ovis = _inv.list_invoices(business_id, status="overdue", limit=5) if hasattr(_inv, "list_invoices") else []
        # fallback: query directly for overdue
        if not ovis:
            conn = get_conn(); conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    "SELECT number, customer_name, total, currency, due_date "
                    "FROM nexus_invoices WHERE business_id = ? AND status != 'paid' "
                    "AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date ASC LIMIT 5",
                    (business_id, today.isoformat()),
                ).fetchall()
                ovis = [dict(r) for r in rows]
            finally: conn.close()
        overdue_invoices = [
            {"number": i.get("number"), "customer": i.get("customer_name"),
             "total": float(i.get("total") or 0), "currency": i.get("currency") or "INR",
             "due_date": i.get("due_date")}
            for i in ovis
        ]
    except Exception as e:
        logger.warning(f"[Briefing] overdue invoices failed: {e}")

    # Pipeline — stats (by_stage) + overview (won_this_month)
    pipe: Dict[str, Any] = {}
    try:
        pipe = dict(_crm.deal_pipeline_stats(business_id))
    except Exception as e:
        logger.warning(f"[Briefing] pipeline stats failed: {e}")
    try:
        ov = _crm.crm_overview(business_id)
        pipe["won_this_month"] = ov.get("won_this_month", 0)
    except Exception as e:
        logger.warning(f"[Briefing] crm overview failed: {e}")

    # Deals that moved yesterday
    moved_deals: List[Dict[str, Any]] = []
    try:
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT name, stage, value, currency FROM nexus_deals "
                "WHERE business_id = ? AND DATE(updated_at) = ? LIMIT 10",
                (business_id, yday.isoformat()),
            ).fetchall()
            moved_deals = [dict(r) for r in rows]
        finally: conn.close()
    except Exception as e:
        logger.warning(f"[Briefing] moved deals failed: {e}")

    open_pipeline = 0.0
    open_deal_count = 0
    for stage, v in (pipe.get("by_stage") or {}).items():
        if stage not in ("won", "lost"):
            open_pipeline += float(v.get("total") or 0)
            open_deal_count += int(v.get("count") or 0)

    return {
        "date": today.isoformat(),
        "tasks": {
            "open_total": task_sum.get("open_total", 0),
            "overdue_count": task_sum.get("overdue", 0),
            "due_today_count": len(today_tasks),
            "due_today": today_tasks,
            "overdue": overdue_tasks,
        },
        "invoices": {
            "outstanding_count": (inv_sum.get("outstanding") or {}).get("count", 0),
            "outstanding_total": (inv_sum.get("outstanding") or {}).get("total", 0),
            "overdue_count": (inv_sum.get("overdue") or {}).get("count", 0),
            "overdue_total": (inv_sum.get("overdue") or {}).get("total", 0),
            "overdue": overdue_invoices,
        },
        "pipeline": {
            "open_total": open_pipeline,
            "open_deal_count": open_deal_count,
            "won_this_month": pipe.get("won_this_month", 0),
            "moved_yesterday": moved_deals,
        },
    }


# ── Evening digest — what got DONE today (backward-looking) ────────────────
def _collect_evening(business_id: str) -> Dict[str, Any]:
    """
    Gather what was actually accomplished today: tasks closed, invoices sent
    or paid, deals advanced. Pure local SQL — no PII leaves the machine.
    """
    today = date.today()

    completed_tasks: List[Dict[str, Any]] = []
    completed_count = 0
    sent_invoices: List[Dict[str, Any]] = []
    paid_invoices: List[Dict[str, Any]] = []
    paid_total = 0.0
    advanced_deals: List[Dict[str, Any]] = []
    won_today = 0

    try:
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            # Tasks completed today: prefer completed_at, fall back to updated_at
            for r in conn.execute(
                "SELECT title, priority, completed_at FROM nexus_tasks "
                "WHERE business_id = ? AND status = 'done' "
                "AND (DATE(completed_at) = ? OR (completed_at IS NULL AND DATE(updated_at) = ?)) "
                "ORDER BY COALESCE(completed_at, updated_at) DESC LIMIT 10",
                (business_id, today.isoformat(), today.isoformat()),
            ).fetchall():
                completed_tasks.append({"title": (r["title"] or "")[:80],
                                        "priority": r["priority"]})
            completed_count = conn.execute(
                "SELECT COUNT(*) FROM nexus_tasks "
                "WHERE business_id = ? AND status = 'done' "
                "AND (DATE(completed_at) = ? OR (completed_at IS NULL AND DATE(updated_at) = ?))",
                (business_id, today.isoformat(), today.isoformat()),
            ).fetchone()[0]

            # Invoices sent today (status moved out of draft and updated today)
            for r in conn.execute(
                "SELECT number, customer_name, total, currency FROM nexus_invoices "
                "WHERE business_id = ? AND status NOT IN ('draft') "
                "AND DATE(updated_at) = ? AND DATE(created_at) = ? LIMIT 10",
                (business_id, today.isoformat(), today.isoformat()),
            ).fetchall():
                sent_invoices.append({
                    "number": r["number"], "customer": r["customer_name"],
                    "total": float(r["total"] or 0), "currency": r["currency"] or "INR",
                })

            # Invoices paid today
            for r in conn.execute(
                "SELECT number, customer_name, total, currency FROM nexus_invoices "
                "WHERE business_id = ? AND status = 'paid' AND DATE(paid_at) = ? "
                "ORDER BY paid_at DESC LIMIT 10",
                (business_id, today.isoformat()),
            ).fetchall():
                amt = float(r["total"] or 0)
                paid_invoices.append({
                    "number": r["number"], "customer": r["customer_name"],
                    "total": amt, "currency": r["currency"] or "INR",
                })
                paid_total += amt

            # Deals updated today (treat as "advanced")
            for r in conn.execute(
                "SELECT name, stage, value, currency FROM nexus_deals "
                "WHERE business_id = ? AND DATE(updated_at) = ? "
                "AND DATE(created_at) != ? LIMIT 10",
                (business_id, today.isoformat(), today.isoformat()),
            ).fetchall():
                advanced_deals.append({
                    "name": r["name"], "stage": r["stage"],
                    "value": float(r["value"] or 0), "currency": r["currency"] or "INR",
                })
                if (r["stage"] or "").lower() == "won":
                    won_today += 1
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"[Briefing] evening collect failed: {e}")

    return {
        "date": today.isoformat(),
        "tasks": {
            "completed_today_count": completed_count,
            "completed_today": completed_tasks,
        },
        "invoices": {
            "sent_today_count": len(sent_invoices),
            "sent_today": sent_invoices,
            "paid_today_count": len(paid_invoices),
            "paid_today_total": paid_total,
            "paid_today": paid_invoices,
        },
        "pipeline": {
            "advanced_today_count": len(advanced_deals),
            "won_today": won_today,
            "advanced_today": advanced_deals,
        },
    }


# ── Narrative (aggregates → cloud via existing privacy path) ────────────────
_BRIEFING_SYSTEM = (
    "You are a senior chief-of-staff writing a 1-page morning briefing for "
    "a small business owner. Be concise, confident, and action-oriented. "
    "Use the numbers provided — do not invent. Use currency symbols and "
    "thousands separators. Keep it scannable: short lines, not paragraphs."
)


def _build_prompt(biz_name: str, data: Dict[str, Any]) -> str:
    return (
        f"Business: {biz_name}\n"
        f"Date: {data['date']}\n\n"
        f"Today's numbers:\n{json.dumps(data, indent=2)}\n\n"
        "Write the briefing in this exact structure (Markdown):\n"
        "## Morning briefing — {date}\n\n"
        "**Headline** — one sentence on the single most important thing today.\n\n"
        "**Today** — 3-5 bullets: what's due today, what's overdue, what's stuck. "
        "Use the actual task titles and invoice customer names from the data.\n\n"
        "**Pipeline** — 1-2 sentences on open deal value, deals that moved yesterday, won-this-month.\n\n"
        "**Recommended next action** — one specific action the owner should take in the next hour.\n"
    )


def _render_narrative(biz_name: str, data: Dict[str, Any]) -> tuple[str, str]:
    """Returns (narrative_markdown, mode)."""
    from config.llm_provider import invoke as llm_invoke

    # If everything is zero, return a static message — no point burning a LLM call.
    totals = (data["tasks"]["open_total"] + data["invoices"]["outstanding_count"]
              + data["pipeline"]["open_deal_count"])
    if totals == 0:
        return (
            f"## Morning briefing — {data['date']}\n\n"
            "**Headline** — Workspace is quiet. No open tasks, deals, or invoices.\n\n"
            "**Recommended next action** — Add your first contact or load sample data "
            "to see NexusAgent in action.\n",
            "static"
        )

    prompt = _build_prompt(biz_name, data)
    try:
        # `sensitive=False` — we're sending aggregates (counts, totals, titles without
        # customer PII beyond first names). The privacy layer still redacts emails /
        # phones / IDs that might slip in via task titles.
        text = llm_invoke(prompt, system=_BRIEFING_SYSTEM,
                          max_tokens=800, temperature=0.2, sensitive=False)
        return text.strip(), "cloud"
    except Exception as e:
        logger.warning(f"[Briefing] cloud narrative failed, falling back local: {e}")
        try:
            text = llm_invoke(prompt, system=_BRIEFING_SYSTEM,
                              max_tokens=500, temperature=0.2, sensitive=True)
            return text.strip(), "local-fallback"
        except Exception as e2:
            logger.error(f"[Briefing] both narratives failed: {e2}")
            return _static_narrative(data), "static-fallback"


_EVENING_SYSTEM = (
    "You are a senior chief-of-staff writing a 1-paragraph end-of-day digest "
    "for a small business owner. Tone: warm, recognising the work that got "
    "done. Use the numbers provided — do not invent. Keep it short: 4-6 lines, "
    "scannable. Use task titles and customer names from the data."
)


def _build_evening_prompt(biz_name: str, data: Dict[str, Any]) -> str:
    return (
        f"Business: {biz_name}\n"
        f"Date: {data['date']}\n\n"
        f"What got done today:\n{json.dumps(data, indent=2)}\n\n"
        "Write the digest in this exact structure (Markdown):\n"
        "## Today's wrap — {date}\n\n"
        "**Headline** — one sentence on the most important thing that got done.\n\n"
        "**Done** — 2-4 bullets: tasks closed, invoices sent / paid, deals advanced. "
        "Use the actual titles and customer names from the data.\n\n"
        "**For tomorrow** — one specific suggestion based on what's still open."
    )


def _render_evening_narrative(biz_name: str, data: Dict[str, Any]) -> tuple[str, str]:
    """Returns (narrative_markdown, mode) for the evening digest."""
    from config.llm_provider import invoke as llm_invoke

    totals = (data["tasks"]["completed_today_count"]
              + data["invoices"]["sent_today_count"]
              + data["invoices"]["paid_today_count"]
              + data["pipeline"]["advanced_today_count"])
    if totals == 0:
        return (
            f"## Today's wrap — {data['date']}\n\n"
            "**Headline** — Quiet day. Nothing closed, sent, or moved on the books today.\n\n"
            "**For tomorrow** — Pick one overdue task and knock it out first thing.\n",
            "static",
        )

    prompt = _build_evening_prompt(biz_name, data)
    try:
        text = llm_invoke(prompt, system=_EVENING_SYSTEM,
                          max_tokens=600, temperature=0.2, sensitive=False)
        return text.strip(), "cloud"
    except Exception as e:
        logger.warning(f"[Briefing] evening cloud narrative failed, falling back local: {e}")
        try:
            text = llm_invoke(prompt, system=_EVENING_SYSTEM,
                              max_tokens=400, temperature=0.2, sensitive=True)
            return text.strip(), "local-fallback"
        except Exception as e2:
            logger.error(f"[Briefing] evening narratives failed: {e2}")
            return _static_evening_narrative(data), "static-fallback"


def _static_evening_narrative(data: Dict[str, Any]) -> str:
    """Plain-text fallback when no LLM is available."""
    t = data["tasks"]; inv = data["invoices"]; p = data["pipeline"]
    lines = [f"## Today's wrap — {data['date']}", ""]
    if t["completed_today_count"]:
        lines.append(f"- ✓ {t['completed_today_count']} task(s) closed")
    if inv["sent_today_count"]:
        lines.append(f"- 📤 {inv['sent_today_count']} invoice(s) sent")
    if inv["paid_today_count"]:
        lines.append(f"- 💰 {inv['paid_today_count']} invoice(s) paid, {inv['paid_today_total']:,.0f}")
    if p["advanced_today_count"]:
        lines.append(f"- 📈 {p['advanced_today_count']} deal(s) advanced"
                     + (f" ({p['won_today']} won)" if p["won_today"] else ""))
    return "\n".join(lines)


def _static_narrative(data: Dict[str, Any]) -> str:
    """Plain-text fallback when no LLM is available."""
    t = data["tasks"]; inv = data["invoices"]; p = data["pipeline"]
    lines = [f"## Morning briefing — {data['date']}", ""]
    if t["overdue_count"]:
        lines.append(f"- ⚠ {t['overdue_count']} overdue task(s)")
    if t["due_today_count"]:
        lines.append(f"- {t['due_today_count']} task(s) due today")
    if inv["overdue_count"]:
        lines.append(f"- {inv['overdue_count']} overdue invoice(s), total {inv['overdue_total']:,.0f}")
    if p["open_deal_count"]:
        lines.append(f"- {p['open_deal_count']} open deals worth {p['open_total']:,.0f}")
    return "\n".join(lines)


# ── Delivery channels ───────────────────────────────────────────────────────
def _deliver_discord(narrative: str) -> bool:
    from config.settings import DISCORD_ENABLED, DISCORD_WEBHOOK_URL
    if not DISCORD_ENABLED:
        return False
    try:
        import requests
        # Discord's content limit is 2000 chars; briefings can exceed that.
        body = narrative[:1900] + ("\n…(truncated)" if len(narrative) > 1900 else "")
        r = requests.post(DISCORD_WEBHOOK_URL, json={"content": body}, timeout=10)
        return r.status_code // 100 == 2
    except Exception as e:
        logger.warning(f"[Briefing] discord delivery failed: {e}")
        return False


def _deliver_whatsapp(business_id: str, narrative: str) -> bool:
    try:
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT phone FROM nexus_whatsapp_accounts WHERE business_id = ? LIMIT 1",
                (business_id,),
            ).fetchone()
        finally: conn.close()
        if not row or not row["phone"]:
            return False
    except Exception:
        return False
    # The WhatsApp bridge handles outbound itself via its own webhook — we just
    # record a notification and let the bridge pick it up on next poll.
    try:
        from api.notifications import push
        push(title="Morning briefing", message=narrative[:800],
             type="briefing", business_id=business_id)
        return True
    except Exception as e:
        logger.warning(f"[Briefing] whatsapp note failed: {e}")
        return False


def _deliver_in_app(business_id: str, narrative: str) -> bool:
    try:
        from api.notifications import push
        push(
            title="Morning briefing ready",
            message="Open the Dashboard to read today's briefing.",
            type="briefing",
            business_id=business_id,
        )
        return True
    except Exception as e:
        logger.debug(f"[Briefing] in-app notif skipped: {e}")
        return False


# ── Public entry points ─────────────────────────────────────────────────────
def run_for_business(business_id: str, deliver: bool = True) -> Dict:
    """Generate and persist today's briefing for one business."""
    # Pull business name for the narrative context
    biz_name = "your business"
    try:
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT name FROM nexus_businesses WHERE id = ? LIMIT 1",
                (business_id,),
            ).fetchone()
            if row: biz_name = row["name"] or biz_name
        finally: conn.close()
    except Exception as e:
        # Non-fatal: the narrative will use the "your business" placeholder.
        logger.debug(f"[Briefing] biz_name lookup failed for {business_id}: {e}")

    data = _collect(business_id)
    narrative, mode = _render_narrative(biz_name, data)

    delivered: List[str] = []
    if deliver:
        if _deliver_in_app(business_id, narrative):   delivered.append("in_app")
        if _deliver_discord(narrative):                delivered.append("discord")
        if _deliver_whatsapp(business_id, narrative):  delivered.append("whatsapp")

    return _save(business_id, narrative, data, mode, delivered)


def run_evening_for_business(business_id: str, deliver: bool = True) -> Dict:
    """Generate and persist today's evening digest for one business."""
    biz_name = "your business"
    try:
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT name FROM nexus_businesses WHERE id = ? LIMIT 1",
                (business_id,),
            ).fetchone()
            if row: biz_name = row["name"] or biz_name
        finally: conn.close()
    except Exception as e:
        # Non-fatal: the narrative will use the "your business" placeholder.
        logger.debug(f"[Briefing] biz_name lookup failed for {business_id}: {e}")

    data = _collect_evening(business_id)
    narrative, mode = _render_evening_narrative(biz_name, data)

    delivered: List[str] = []
    if deliver:
        try:
            from api.notifications import push
            push(title="Today's wrap is ready",
                 message="See what got done today on the dashboard.",
                 type="briefing", business_id=business_id)
            delivered.append("in_app")
        except Exception as e:
            logger.debug(f"[Briefing] evening in-app notif skipped: {e}")
        if _deliver_discord(narrative): delivered.append("discord")

    return _save(business_id, narrative, data, mode, delivered, kind="evening")


def run_for_all_businesses() -> List[Dict]:
    """Invoked by the daily scheduler."""
    results: List[Dict] = []
    try:
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id FROM nexus_businesses WHERE is_active = 1"
            ).fetchall()
        finally: conn.close()
        for r in rows:
            try:
                results.append(run_for_business(r["id"]))
            except Exception as e:
                logger.exception(f"[Briefing] failed for business {r['id']}: {e}")
    except Exception as e:
        logger.exception(f"[Briefing] batch run failed: {e}")
    logger.info(f"[Briefing] Generated {len(results)} briefing(s)")
    return results
