"""Outreach — bulk personalized messaging across WhatsApp / email.

Pairs with Lead Hunter to close the full prospecting loop:
    Lead Hunter      — finds N businesses matching your ICP
    Outreach         — drafts a personalized message per contact and sends
                       in batches with rate limiting + approval flow

Two-step flow keeps the user in control:
    1. preview run (confirm=False) — drafts everything, returns a sample
       so the user can sanity-check the tone + targeting
    2. send run    (confirm=True)  — actually delivers + logs each as a
       CRM interaction

Personalization strategy: one LLM call generates a base template using the
business's profile + the user's intent. Per-contact substitution then fills
{{first_name}} / {{business_type}} / {{city}} placeholders. This keeps the
tool fast (1 LLM call regardless of segment size) and deterministic.
A future v2 can switch to per-contact LLM personalization for premium tiers.
"""
from __future__ import annotations

import re
import sqlite3  # sqlite3.Row sentinel
import time
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from agents.tool_registry import register_tool
from config.db import get_conn


# ── Segment querying ────────────────────────────────────────────────────────
def _filter_contacts(business_id: str, segment: Dict[str, Any],
                      max_n: int) -> List[Dict[str, Any]]:
    """Return contacts matching the segment filters.

    Supported keys in `segment`:
        tag             — exact tag match (e.g. 'lead-hunter')
        source          — exact source match in notes (free-text contains)
        has_phone       — bool, true = require phone
        has_email       — bool, true = require email
        never_contacted — bool, true = no rows in nexus_interactions
        not_contacted_days — int, true if no interaction in last N days
    """
    from api.crm import CONTACTS_TABLE, INTERACTIONS_TABLE

    sql = (f"SELECT c.* FROM {CONTACTS_TABLE} c "
           f"WHERE c.business_id = ?")
    params: list = [business_id]

    if segment.get("tag"):
        sql += " AND c.tags LIKE ?"
        params.append(f"%{segment['tag']}%")

    if segment.get("has_phone"):
        sql += " AND c.phone IS NOT NULL AND c.phone != ''"

    if segment.get("has_email"):
        sql += " AND c.email IS NOT NULL AND c.email != ''"

    if segment.get("source"):
        sql += " AND c.notes LIKE ?"
        params.append(f"%{segment['source']}%")

    # never_contacted vs not_contacted_days are mutually exclusive
    if segment.get("never_contacted"):
        sql += (f" AND NOT EXISTS (SELECT 1 FROM {INTERACTIONS_TABLE} i "
                f"WHERE i.contact_id = c.id AND i.business_id = c.business_id)")
    elif segment.get("not_contacted_days"):
        days = int(segment["not_contacted_days"])
        # Use parameterised SQL to keep this DB-engine-agnostic
        sql += (f" AND NOT EXISTS (SELECT 1 FROM {INTERACTIONS_TABLE} i "
                f"WHERE i.contact_id = c.id AND i.business_id = c.business_id "
                f"AND i.occurred_at > datetime('now', '-' || ? || ' days'))")
        params.append(str(days))

    sql += " ORDER BY c.created_at DESC LIMIT ?"
    params.append(max_n)

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# ── Template generation ────────────────────────────────────────────────────
def _build_template(business_id: str, intent: str, channel: str,
                     sample_contact: Optional[Dict[str, Any]]) -> str:
    """One LLM call → one base template with {{placeholders}}."""
    from config import llm_provider

    business_name  = "our business"
    business_blurb = ""
    try:
        from api.businesses import get_business
        biz = get_business(business_id) or {}
        business_name = biz.get("name") or business_name
        for k in ("description", "about", "blurb", "notes"):
            if biz.get(k):
                business_blurb = biz[k].strip()
                break
    except Exception:
        pass

    sample_hint = ""
    if sample_contact:
        sample_hint = (
            f"\n\nFor reference, one of the recipients looks like: "
            f"name='{sample_contact.get('first_name','')} {sample_contact.get('last_name','')}', "
            f"title='{sample_contact.get('title','')}', "
            f"notes='{(sample_contact.get('notes') or '')[:200]}'"
        )

    if channel == "whatsapp":
        channel_hint = (
            "Write for WhatsApp. Casual, ~2-3 short sentences max. "
            "No subject line. End with a clear soft call to action."
        )
    else:
        channel_hint = (
            "Write a short cold email. ~4-5 sentences. Include a one-line "
            "subject at the very top prefixed with 'Subject: '. End with a "
            "clear soft call to action."
        )

    system = (
        "You are an outreach copywriter for an Indian SMB. Write a SHORT, "
        "personalized message that doesn't feel like spam. Use the placeholder "
        "{{first_name}} where the recipient's name should appear. If the "
        "business type / category fits naturally, use {{business_type}}. "
        "Don't invent details about the recipient. Keep it human."
    )
    prompt = (
        f"Sender: {business_name}\n"
        f"Sender's offering: {business_blurb or '(not specified)'}\n\n"
        f"Outreach goal: {intent}\n\n"
        f"{channel_hint}{sample_hint}\n\n"
        f"Output the message body only, with {{{{first_name}}}} placeholder. "
        f"No surrounding quotes or commentary."
    )
    try:
        # Drafting is creative work — let the router send it to cloud if available
        text = llm_provider.invoke(prompt, system=system, max_tokens=400, temperature=0.6)
    except Exception as e:
        logger.warning(f"[outreach] template LLM call failed: {e}")
        # Fallback to a plain template so the tool still works locally
        text = (
            f"Hi {{{{first_name}}}}, this is from {business_name}. "
            f"{intent}. Would love to chat — let me know if interested."
        )
    return text.strip()


# ── Per-contact placeholder substitution ───────────────────────────────────
def _personalize(template: str, contact: Dict[str, Any]) -> str:
    first = (contact.get("first_name") or "there").strip() or "there"
    title = (contact.get("title") or "").strip()
    notes = (contact.get("notes") or "").strip()

    # Best-effort business_type guess from title or notes
    btype = title or "your business"
    msg = (template
           .replace("{{first_name}}",   first)
           .replace("{{business_type}}", btype)
           .replace("{{name}}",          first))
    return msg


def _full_name(c: Dict[str, Any]) -> str:
    return " ".join(filter(None, [c.get("first_name"), c.get("last_name")])).strip() or "(unnamed)"


# ── Sender adapters ────────────────────────────────────────────────────────
def _send_whatsapp(to_phone: str, body: str) -> None:
    from api.whatsapp import send_outbound
    send_outbound(to_phone, body)


def _send_email(to_addr: str, body: str) -> None:
    """Sends via the same Gmail SMTP path used by the existing send_email tool."""
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    if not EMAIL_ENABLED:
        raise RuntimeError("Email is not configured (set GMAIL_USER + GMAIL_APP_PASSWORD)")

    # The body may contain a "Subject: foo" first line we generated above
    subject = "Hello from " + (GMAIL_USER.split("@")[0] if GMAIL_USER else "us")
    msg_body = body
    first_line, _, rest = body.partition("\n")
    if first_line.lower().startswith("subject:"):
        subject = first_line.split(":", 1)[1].strip() or subject
        msg_body = rest.lstrip()

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(msg_body, "plain"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)


# ── The tool ───────────────────────────────────────────────────────────────
def _outreach_campaign(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    user_id     = ctx["user_id"]

    intent  = (args.get("intent") or "").strip()
    if not intent:
        raise ValueError("'intent' is required — describe what to say to recipients.")

    channel = (args.get("channel") or "whatsapp").lower()
    if channel not in ("whatsapp", "email"):
        raise ValueError("channel must be 'whatsapp' or 'email'")

    segment = args.get("segment") or {}
    if not isinstance(segment, dict):
        raise ValueError("segment must be an object")

    confirm  = bool(args.get("confirm", False))
    max_send = max(1, min(int(args.get("max_send", 25)), 100))

    # Auto-require the right contact field for the channel
    if channel == "whatsapp":
        segment.setdefault("has_phone", True)
    else:
        segment.setdefault("has_email", True)

    contacts = _filter_contacts(business_id, segment, max_send)
    if not contacts:
        return {
            "ok":      True,
            "matched": 0,
            "channel": channel,
            "message": "No contacts matched that segment. Try loosening the filters.",
        }

    # One LLM call → base template
    template = _build_template(business_id, intent, channel, contacts[0])

    drafts: List[Dict[str, Any]] = []
    for c in contacts:
        msg = _personalize(template, c)
        addr = (c.get("phone") if channel == "whatsapp" else c.get("email")) or ""
        drafts.append({
            "contact_id": c["id"],
            "name":       _full_name(c),
            "to":         addr,
            "message":    msg,
        })

    # Preview mode
    if not confirm:
        sample = [
            {"name": d["name"], "to": d["to"], "message": d["message"]}
            for d in drafts[:3]
        ]
        return {
            "ok":            True,
            "matched":       len(drafts),
            "channel":       channel,
            "preview":       sample,
            "more":          max(0, len(drafts) - len(sample)),
            "campaign_hint": (
                f"Drafted {len(drafts)} {channel} message(s). The first "
                f"{len(sample)} are shown above. Reply 'send all' (or call "
                f"this tool again with confirm=true) to deliver."
            ),
            "message":       (
                f"Drafted {len(drafts)} personalized {channel} messages. "
                f"Confirm to send."
            ),
        }

    # Send mode — rate-limited
    sent: List[str] = []
    failed: List[Dict[str, Any]] = []
    delay_s = 1.5 if channel == "whatsapp" else 0.5
    campaign_id = f"oc-{uuid.uuid4().hex[:10]}"

    for i, d in enumerate(drafts):
        if not d["to"]:
            failed.append({"name": d["name"], "reason": "missing contact info"})
            continue
        try:
            if channel == "whatsapp":
                _send_whatsapp(d["to"], d["message"])
            else:
                _send_email(d["to"], d["message"])

            # Mirror as CRM interaction so the contact's timeline shows the touch.
            # WhatsApp doesn't have a dedicated interaction type — use 'note'.
            try:
                from api import crm
                crm.create_interaction(business_id, user_id, {
                    "type":       "email" if channel == "email" else "note",
                    "subject":    f"Outreach via {channel} (campaign {campaign_id})",
                    "summary":    d["message"][:1000],
                    "contact_id": d["contact_id"],
                })
            except Exception as e:
                logger.warning(f"[outreach] interaction log failed for {d['name']}: {e}")

            sent.append(d["contact_id"])
        except Exception as e:
            logger.warning(f"[outreach] send failed → {d['name']} ({d['to']}): {e}")
            failed.append({"name": d["name"], "reason": str(e)[:120]})

        # Small delay between sends — keeps WhatsApp from flagging burst behavior
        if i < len(drafts) - 1:
            time.sleep(delay_s)

    return {
        "ok":          True,
        "campaign_id": campaign_id,
        "channel":     channel,
        "sent":        len(sent),
        "failed":      len(failed),
        "errors":      failed[:5],
        "more_errors": max(0, len(failed) - 5),
        "message":     (
            f"Campaign {campaign_id}: sent {len(sent)} via {channel}, "
            f"{len(failed)} failed. Each delivery is logged in the CRM."
        ),
    }


register_tool(
    name="outreach_campaign",
    description=(
        "Send a personalized outreach message (WhatsApp or email) to a "
        "segment of CRM contacts. Use to follow up with leads after they've "
        "been added — e.g. 'message all lead-hunter contacts about our "
        "printing services' or 'email all overdue invoice contacts a "
        "reminder'. Defaults to PREVIEW mode (drafts only, returns a sample "
        "for review). Set confirm=true to actually send. Each delivery is "
        "rate-limited and logged as a CRM interaction. Generates ONE base "
        "template with {{first_name}} substitution — predictable + fast."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": (
                    "Free text describing what to say. e.g. 'introduce our "
                    "B2B printing services and offer a free sample pack', or "
                    "'remind them about the upcoming festival catalog'. The "
                    "LLM uses this + your business profile to draft the template."
                ),
            },
            "channel": {
                "type": "string",
                "enum":        ["whatsapp", "email"],
                "description": "Delivery channel. Default 'whatsapp'.",
                "default":     "whatsapp",
            },
            "segment": {
                "type": "object",
                "description": (
                    "Filters for which contacts to target. All keys optional. "
                    "Common: tag (e.g. 'lead-hunter'), source (free-text "
                    "match in notes), never_contacted (bool — no past "
                    "interactions), not_contacted_days (int — last touch "
                    "older than N days)."
                ),
                "properties": {
                    "tag":                {"type": "string"},
                    "source":             {"type": "string"},
                    "has_phone":          {"type": "boolean"},
                    "has_email":          {"type": "boolean"},
                    "never_contacted":    {"type": "boolean"},
                    "not_contacted_days": {"type": "integer"},
                },
            },
            "max_send": {
                "type": "integer",
                "description": "Cap on number of messages this run (1-100). Default 25.",
                "default":     25,
            },
            "confirm": {
                "type": "boolean",
                "description": (
                    "If false (default), just return a preview of the drafts. "
                    "If true, actually send the messages with rate limiting."
                ),
                "default": False,
            },
        },
        "required": ["intent"],
    },
    handler=_outreach_campaign,
    summary_fn=lambda a: (
        f"Outreach: {a.get('channel','whatsapp')} → "
        f"{(a.get('intent') or '')[:60]}"
        + (" (SEND)" if a.get("confirm") else " (preview)")
    ),
)
