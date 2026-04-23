"""
Meeting prep agent — every 10 minutes, look ahead ~30 min for upcoming
Google Calendar events. For each imminent meeting, build a brief and push
an in-app notification so the user opens the app prepared.

The brief pulls:
- Attendees — matched against CRM contacts/companies
- Recent interactions with them
- Open deals linked to the matched contacts/companies
- Any business memory entries mentioning the attendees

Privacy:
- Runs only for users who have connected Google Calendar.
- Only reads data within the user's business scope.
- Pushes ONE notification per event per day to avoid spam.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger

from config.settings import DB_PATH

LOOKAHEAD_MINUTES = 45
TAG = "meeting-prep"


def _already_notified(business_id: str, event_id: str) -> bool:
    """Check whether we already pushed a prep for this event today."""
    from api.notifications import TABLE as NOTIF_TABLE
    today = datetime.utcnow().date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            f"SELECT 1 FROM {NOTIF_TABLE} WHERE business_id = ? "
            f"AND type = ? AND metadata LIKE ? AND DATE(created_at) = ? LIMIT 1",
            (business_id, TAG, f"%{event_id}%", today),
        ).fetchone()
    finally:
        conn.close()
    return bool(row)


def _extract_emails(events: list) -> set:
    """Collect the set of attendee + organizer emails across events."""
    # Events come from the Google API via api.calendar — we only see organizer
    # and attendees_count from our own light wrapper. Pull the organizer here;
    # for richer attendee parsing, tweak api.calendar.list_upcoming_events.
    emails = set()
    for ev in events or []:
        if ev.get("organizer_email"):
            emails.add(ev["organizer_email"].strip().lower())
    return emails


def _build_brief(business_id: str, event: dict) -> str:
    """Compose a compact prep note for a single event."""
    from api import crm as _crm
    from agents.business_memory import list_memory

    lines = []
    when = event.get("start", "")
    where = event.get("location") or ""
    lines.append(f"*{event.get('summary', '(no title)')}* — {when[:16]}" + (f" @ {where}" if where else ""))

    organizer = (event.get("organizer_email") or "").lower()
    matched_contacts = []
    if organizer:
        try:
            matched_contacts = _crm.list_contacts(business_id, search=organizer, limit=3)
        except Exception:
            matched_contacts = []

    if matched_contacts:
        c = matched_contacts[0]
        name = (c.get("first_name", "") + " " + c.get("last_name", "")).strip()
        lines.append(f"Likely attendee: {name} ({c.get('title', '')}) at {c.get('company_name', '?')}")
        # Recent interactions
        try:
            interactions = _crm.list_interactions(business_id, contact_id=c["id"], limit=3)
            if interactions:
                lines.append("Recent interactions:")
                for it in interactions:
                    lines.append(f"  • {it.get('type', '')}: {it.get('subject', '')[:60]} ({it.get('occurred_at', '')[:10]})")
        except Exception:
            pass
        # Open deals
        try:
            open_deals = [d for d in _crm.list_deals(business_id, limit=100)
                          if d.get("contact_id") == c["id"] and d.get("stage") not in ("won", "lost")]
            if open_deals:
                lines.append(f"Open deals: " + ", ".join(f"{d['name']} ({d['stage']})" for d in open_deals[:3]))
        except Exception:
            pass
    elif organizer:
        lines.append(f"No CRM match for {organizer} — consider adding them as a contact.")

    # Keyword search memory for any attendee name / company name
    if matched_contacts:
        c = matched_contacts[0]
        keyword = c.get("company_name") or c.get("last_name") or ""
        if keyword and len(keyword) > 2:
            try:
                memos = list_memory(business_id, search=keyword, limit=3)
                if memos:
                    lines.append("Relevant memory:")
                    for m in memos:
                        lines.append(f"  • {m['content'][:120]}")
            except Exception:
                pass

    return "\n".join(lines)


def run_for_user(user_id: str, business_id: str) -> dict:
    """Check this user's calendar; push briefs for meetings starting soon."""
    from api import calendar as _cal
    from api import notifications as _notifs

    try:
        conn = _cal.get_connection(user_id)
    except Exception:
        conn = None
    if not conn:
        return {"user_id": user_id, "skipped": "not connected", "pushed": 0}

    try:
        events = _cal.list_upcoming_events(user_id, days_ahead=1, max_results=10)
    except Exception as e:
        logger.debug(f"[MeetingPrep] Calendar fetch failed for {user_id}: {e}")
        return {"user_id": user_id, "error": str(e), "pushed": 0}

    now = datetime.now(timezone.utc)
    horizon = now + timedelta(minutes=LOOKAHEAD_MINUTES)
    pushed = 0

    for ev in events:
        start_str = ev.get("start")
        if not start_str:
            continue
        try:
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        except Exception:
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if start < now or start > horizon:
            continue
        if _already_notified(business_id, ev.get("id", "")):
            continue

        brief = _build_brief(business_id, ev)
        import json
        try:
            _notifs.push(
                title=f"Meeting in {int((start - now).total_seconds() / 60)} min: {ev.get('summary', '')[:80]}",
                message=brief[:900],
                severity="info",
                type=TAG,
                user_id=user_id,
                business_id=business_id,
                metadata={"event_id": ev.get("id", "")},
            )
            pushed += 1
        except Exception as e:
            logger.warning(f"[MeetingPrep] push failed: {e}")

    return {"user_id": user_id, "events_checked": len(events), "pushed": pushed}


def run_for_all() -> list:
    """Iterate every user/business pair that has a calendar connection."""
    from api.calendar import CAL_TABLE
    from api.businesses import MEMBERS_TABLE
    results = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT user_id FROM {CAL_TABLE}",
        ).fetchall()
    finally:
        conn.close()

    for r in rows:
        user_id = r["user_id"]
        # For each business this user is a member of, run once. In practice
        # most users have one business, but we handle the multi-business case.
        conn2 = sqlite3.connect(DB_PATH)
        try:
            biz_rows = conn2.execute(
                f"SELECT business_id FROM {MEMBERS_TABLE} WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        finally:
            conn2.close()
        for br in biz_rows:
            try:
                results.append(run_for_user(user_id, br[0]))
            except Exception as e:
                logger.warning(f"[MeetingPrep] failed for {user_id}/{br[0]}: {e}")
    return results
