"""
Unified agent activity feed.

Collects recent actions from every autonomous agent into a single timeline so
the UI can show: "who did what, when, and where the outcome lives". Each event
is stamped with the agent's current persona (name + role tag) so renamed
agents reflect the user's customisation everywhere.

Sources (one per agent):
    Atlas  (morning_briefing)    — nexus_briefings
    Kira   (invoice_reminder)    — nexus_agent_approvals where tool=send_invoice_email
    Iris   (email_triage)        — nexus_email_triage_log
    Arjun  (stale_deal_watcher)  — nexus_notifications titled "Stale deals…"
    Sage   (meeting_prep)        — nexus_notifications where type='meeting-prep'

Memory-keeper (Echo) has no persistent per-run output yet — it's weekly and
silent. It'll appear here once it emits a summary record.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta
from typing import Dict, List

from loguru import logger

from agents.personas import get_persona
from config.settings import DB_PATH
from utils.timez import now_utc_naive


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _attach_persona(event: Dict, business_id: str) -> Dict:
    p = get_persona(business_id, event["agent_key"])
    event["agent_name"]     = p["name"]
    event["agent_role_tag"] = p["role_tag"]
    event["agent_emoji"]    = p["emoji"]
    return event


# ── Per-agent collectors ────────────────────────────────────────────────────
def _from_briefings(business_id: str, since: str) -> List[Dict]:
    out: List[Dict] = []
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, narrative_mode FROM nexus_briefings "
                "WHERE business_id = ? AND created_at > ? "
                "ORDER BY created_at DESC LIMIT 20",
                (business_id, since),
            ).fetchall()
    except sqlite3.OperationalError:
        return out  # table may not exist yet
    for r in rows:
        out.append({
            "id":         f"brief-{r['id']}",
            "ts":         r["created_at"],
            "agent_key":  "morning_briefing",
            "title":      "Wrote your morning briefing",
            "summary":    f"Generated via {r['narrative_mode']} path — aggregates only.",
            "surface":    "/",
            "status":     "done",
        })
    return out


def _from_invoice_approvals(business_id: str, since: str) -> List[Dict]:
    out: List[Dict] = []
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT id, summary, status, created_at "
                "FROM nexus_agent_approvals "
                "WHERE business_id = ? AND tool_name = 'send_invoice_email' "
                "AND created_at > ? ORDER BY created_at DESC LIMIT 20",
                (business_id, since),
            ).fetchall()
    except sqlite3.OperationalError:
        return out
    for r in rows:
        status = r["status"] or "pending"
        verb = {
            "pending":  "Drafted a reminder email",
            "approved": "Sent reminder (after your approval)",
            "denied":   "Drafted reminder — you declined",
            "expired":  "Drafted reminder — expired unseen",
        }.get(status, "Drafted a reminder email")
        out.append({
            "id":        f"inv-{r['id']}",
            "ts":        r["created_at"],
            "agent_key": "invoice_reminder",
            "title":     verb,
            "summary":   r["summary"] or "",
            "surface":   "/approvals",
            "status":    status,
        })
    return out


def _from_email_triage(business_id: str, since: str) -> List[Dict]:
    out: List[Dict] = []
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT id, sender, subject, classification, urgency, processed_at "
                "FROM nexus_email_triage_log "
                "WHERE business_id = ? AND processed_at > ? "
                "ORDER BY processed_at DESC LIMIT 15",
                (business_id, since),
            ).fetchall()
    except sqlite3.OperationalError:
        return out
    for r in rows:
        classification = r["classification"] or "general"
        urgency = r["urgency"] or ""
        sender = (r["sender"] or "").split("<")[0].strip()[:60]
        subject = (r["subject"] or "").strip()[:70]
        out.append({
            "id":        f"triage-{r['id']}",
            "ts":        r["processed_at"],
            "agent_key": "email_triage",
            "title":     f"Triaged email from {sender or 'unknown'}",
            "summary":   f"[{classification}{' · '+urgency if urgency else ''}] {subject}",
            "surface":   "/approvals",
            "status":    "done",
        })
    return out


def _from_notifications(business_id: str, since: str) -> List[Dict]:
    """Stale-deal-watcher and meeting-prep both land in notifications."""
    out: List[Dict] = []
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT id, type, title, message, created_at "
                "FROM nexus_notifications "
                "WHERE business_id = ? AND created_at > ? "
                "AND (type = 'agent' OR type = 'meeting-prep' OR type = 'briefing') "
                "ORDER BY created_at DESC LIMIT 30",
                (business_id, since),
            ).fetchall()
    except sqlite3.OperationalError:
        return out
    for r in rows:
        title = r["title"] or ""
        ntype = r["type"] or ""
        # Route to the right agent by content pattern
        if ntype == "meeting-prep":
            agent = "meeting_prep"
            verb = "Prepared a meeting brief"
        elif ntype == "briefing":
            # Already covered by _from_briefings — skip to avoid dupes
            continue
        elif "stale" in title.lower() or "stalled" in title.lower():
            agent = "stale_deal_watcher"
            verb = "Flagged stalled deals"
        elif "invoice reminder" in title.lower() or "reminder" in title.lower():
            # Already covered by _from_invoice_approvals — skip
            continue
        else:
            continue  # unknown generic agent notif — skip rather than mis-attribute
        out.append({
            "id":        f"notif-{r['id']}",
            "ts":        r["created_at"],
            "agent_key": agent,
            "title":     verb,
            "summary":   r["message"] or title,
            "surface":   "/" if agent == "stale_deal_watcher" else "/",
            "status":    "done",
        })
    return out


# ── Public entry ────────────────────────────────────────────────────────────
def recent(business_id: str, hours: int = 48, limit: int = 50) -> List[Dict]:
    """
    Return recent agent activity, newest first, across all agents.
    Each event carries agent_name + role_tag + emoji resolved from personas.
    """
    since = (now_utc_naive() - timedelta(hours=hours)).isoformat()
    events: List[Dict] = []
    for fn in (_from_briefings, _from_invoice_approvals, _from_email_triage, _from_notifications):
        try:
            events.extend(fn(business_id, since))
        except Exception as e:
            logger.warning(f"[Activity] collector {fn.__name__} failed: {e}")

    # Sort newest first, then stamp with current persona
    events.sort(key=lambda e: e.get("ts") or "", reverse=True)
    events = events[:limit]
    return [_attach_persona(e, business_id) for e in events]
