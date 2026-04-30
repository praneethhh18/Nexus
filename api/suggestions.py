"""
AI suggestions — passive, per-record nudges that surface patterns the user
might otherwise miss.

Rule-based first (fast, predictable, free). LLM-backed suggestions can be
layered on later by replacing `_rule_suggestions` with a thin LLM call.

A suggestion is a small dict:
    {
      "id":          stable hash of (entity_type, entity_id, rule_key),
      "entity_type": 'contact' | 'deal' | 'invoice' | 'task',
      "entity_id":   record id,
      "rule_key":    machine identifier for the rule that fired,
      "agent":       which agent persona "voiced" this (for the UI)
      "severity":    'info' | 'warn' | 'high',
      "title":       short line to show
      "detail":      one-sentence explanation
      "cta":         optional next-step hint
    }

Dismissals persist in `nexus_suggestion_dismissals` so repeat runs don't
re-raise a nudge the user already waved off.
"""
from __future__ import annotations

import hashlib
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime, timedelta, date
from typing import Dict, List

from loguru import logger

from config.db import get_conn
from utils.timez import now_iso, now_utc_naive

DISMISS_TABLE = "nexus_suggestion_dismissals"

VALID_ENTITY_TYPES = {"contact", "deal", "invoice", "task"}


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {DISMISS_TABLE} (
            business_id  TEXT NOT NULL,
            suggestion_id TEXT NOT NULL,
            dismissed_at TEXT NOT NULL,
            PRIMARY KEY (business_id, suggestion_id)
        )
    """)
    conn.commit()
    return conn


def _suggestion_id(entity_type: str, entity_id: str, rule_key: str) -> str:
    raw = f"{entity_type}:{entity_id}:{rule_key}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _is_dismissed(business_id: str, sid: str) -> bool:
    conn = _conn()
    try:
        row = conn.execute(
            f"SELECT 1 FROM {DISMISS_TABLE} WHERE business_id = ? AND suggestion_id = ?",
            (business_id, sid),
        ).fetchone()
    finally:
        conn.close()
    return bool(row)


def dismiss(business_id: str, suggestion_id: str) -> None:
    conn = _conn()
    try:
        # Portable: ON CONFLICT works on SQLite 3.24+ and Postgres.
        conn.execute(
            f"INSERT INTO {DISMISS_TABLE} "
            f"(business_id, suggestion_id, dismissed_at) VALUES (?, ?, ?) "
            f"ON CONFLICT (business_id, suggestion_id) DO NOTHING",
            (business_id, suggestion_id, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


# ── Rule implementations ────────────────────────────────────────────────────
def _contact_suggestions(conn, business_id: str, contact_id: str) -> List[Dict]:
    out: List[Dict] = []
    row = conn.execute(
        "SELECT first_name, last_name, created_at FROM nexus_contacts "
        "WHERE id = ? AND business_id = ?",
        (contact_id, business_id),
    ).fetchone()
    if not row:
        return out
    name = f"{row['first_name'] or ''} {row['last_name'] or ''}".strip() or "this contact"

    # Rule: no task referencing this contact in the last 21 days → follow-up overdue
    try:
        cutoff = (now_utc_naive() - timedelta(days=21)).isoformat()
        last_task = conn.execute(
            "SELECT MAX(created_at) FROM nexus_tasks "
            "WHERE business_id = ? AND contact_id = ?",
            (business_id, contact_id),
        ).fetchone()[0]
        if not last_task or last_task < cutoff:
            out.append({
                "rule_key":    "contact_followup_overdue",
                "agent":       "Sage",
                "severity":    "info",
                "title":       "Follow-up overdue",
                "detail":      f"No task referencing {name} in the last 3 weeks.",
                "cta":         "Create a follow-up task",
            })
    except Exception as e:
        logger.debug(f"[suggestions] contact_followup check failed: {e}")

    # Rule: contact linked to an open overdue invoice → chase
    try:
        today = date.today().isoformat()
        overdue = conn.execute(
            "SELECT number, total FROM nexus_invoices "
            "WHERE business_id = ? AND customer_contact_id = ? "
            "AND status = 'sent' AND due_date < ? LIMIT 1",
            (business_id, contact_id, today),
        ).fetchone()
        if overdue:
            out.append({
                "rule_key":    "contact_has_overdue_invoice",
                "agent":       "Kira",
                "severity":    "warn",
                "title":       "Overdue invoice",
                "detail":      f"Invoice {overdue['number']} for this contact is past due.",
                "cta":         "Draft a reminder email",
            })
    except Exception as e:
        logger.debug(f"[suggestions] contact_overdue_invoice check failed: {e}")

    return out


def _deal_suggestions(conn, business_id: str, deal_id: str) -> List[Dict]:
    out: List[Dict] = []
    row = conn.execute(
        "SELECT name, stage, updated_at, value FROM nexus_deals "
        "WHERE id = ? AND business_id = ?",
        (deal_id, business_id),
    ).fetchone()
    if not row:
        return out

    # Rule: deal hasn't moved in 14 days
    if row["stage"] not in ("won", "lost") and row["updated_at"]:
        try:
            last = datetime.fromisoformat(row["updated_at"])
            if now_utc_naive() - last > timedelta(days=14):
                out.append({
                    "rule_key":    "deal_stale",
                    "agent":       "Arjun",
                    "severity":    "warn",
                    "title":       "Deal stale",
                    "detail":      "This deal hasn't moved stage for 2+ weeks.",
                    "cta":         "Add a next-step task",
                })
        except Exception:
            pass

    return out


def _invoice_suggestions(conn, business_id: str, invoice_id: str) -> List[Dict]:
    out: List[Dict] = []
    inv = conn.execute(
        "SELECT number, status, customer_name, customer_contact_id, due_date, paid_at "
        "FROM nexus_invoices WHERE id = ? AND business_id = ?",
        (invoice_id, business_id),
    ).fetchone()
    if not inv:
        return out

    # Rule: customer has history of paying late (avg payment >7 days after due)
    try:
        if inv["customer_contact_id"]:
            hist = conn.execute(
                "SELECT due_date, paid_at FROM nexus_invoices "
                "WHERE business_id = ? AND customer_contact_id = ? "
                "AND status = 'paid' AND paid_at IS NOT NULL AND due_date IS NOT NULL",
                (business_id, inv["customer_contact_id"]),
            ).fetchall()
            lates = []
            for h in hist:
                try:
                    due = date.fromisoformat(h["due_date"])
                    paid = datetime.fromisoformat(h["paid_at"]).date()
                    lates.append((paid - due).days)
                except Exception:
                    continue
            if lates and sum(lates) / len(lates) > 7:
                out.append({
                    "rule_key":    "invoice_client_pays_late",
                    "agent":       "Kira",
                    "severity":    "info",
                    "title":       "Client typically pays late",
                    "detail":      f"Past {len(lates)} invoice(s) averaged "
                                   f"{sum(lates)//len(lates)} days late.",
                    "cta":         "Send reminder 5 days early",
                })
    except Exception as e:
        logger.debug(f"[suggestions] invoice_pay_history check failed: {e}")

    # Rule: invoice overdue and still 'sent'
    if inv["status"] == "sent" and inv["due_date"]:
        try:
            if date.fromisoformat(inv["due_date"]) < date.today():
                out.append({
                    "rule_key":    "invoice_overdue_now",
                    "agent":       "Kira",
                    "severity":    "high",
                    "title":       "Invoice is overdue",
                    "detail":      "Past the due date with status still 'sent'.",
                    "cta":         "Draft reminder",
                })
        except Exception:
            pass

    return out


def _task_suggestions(conn, business_id: str, task_id: str) -> List[Dict]:
    out: List[Dict] = []
    row = conn.execute(
        "SELECT title, description, status, due_date, priority, created_at "
        "FROM nexus_tasks WHERE id = ? AND business_id = ?",
        (task_id, business_id),
    ).fetchone()
    if not row:
        return out

    # Rule: long description / big task → suggest breaking it down
    desc = row["description"] or ""
    if len(desc) > 600 and row["status"] not in ("done", "cancelled"):
        out.append({
            "rule_key":    "task_large",
            "agent":       "Atlas",
            "severity":    "info",
            "title":       "This task looks big",
            "detail":      "Description is 600+ chars — consider splitting into subtasks.",
            "cta":         "Ask the AI to break it down",
        })

    # Rule: overdue + high priority + still open
    if row["status"] in ("open", "in_progress") and row["due_date"]:
        try:
            if date.fromisoformat(row["due_date"]) < date.today() and row["priority"] in ("high", "urgent"):
                out.append({
                    "rule_key":    "task_overdue_high_priority",
                    "agent":       "Atlas",
                    "severity":    "high",
                    "title":       "Overdue & high priority",
                    "detail":      "This task is past its due date.",
                    "cta":         "Bump or reassign",
                })
        except Exception:
            pass

    return out


_RULES_BY_TYPE = {
    "contact": _contact_suggestions,
    "deal":    _deal_suggestions,
    "invoice": _invoice_suggestions,
    "task":    _task_suggestions,
}


# ── Public API ──────────────────────────────────────────────────────────────
def for_entity(business_id: str, entity_type: str, entity_id: str) -> List[Dict]:
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"Unknown entity_type '{entity_type}'")
    fn = _RULES_BY_TYPE.get(entity_type)
    if not fn:
        return []
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        raw = fn(conn, business_id, entity_id)
    finally:
        conn.close()

    out = []
    for r in raw:
        sid = _suggestion_id(entity_type, entity_id, r["rule_key"])
        if _is_dismissed(business_id, sid):
            continue
        out.append({
            "id":          sid,
            "entity_type": entity_type,
            "entity_id":   entity_id,
            **r,
        })
    return out
