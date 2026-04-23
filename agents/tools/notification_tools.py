"""Notification + email tools for the agent."""
from __future__ import annotations

from agents.tool_registry import register_tool


def _send_slack(ctx, args):
    from action_tools.slack_tool import send_alert
    sent = send_alert(
        title=args["title"],
        message=args["message"],
        severity=args.get("severity", "info"),
        business_id=ctx["business_id"],
        user_id=ctx["user_id"],
    )
    return {"sent": sent}


register_tool(
    name="send_slack",
    description=(
        "Post a message to the business's configured Slack channel. Only works "
        "if SLACK_WEBHOOK_URL is set. Use for team alerts, not customer messages."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["info", "warning", "critical", "success"], "default": "info"},
        },
        "required": ["title", "message"],
    },
    handler=_send_slack,
    summary_fn=lambda a: f"Slack post: [{a.get('severity', 'info')}] {a.get('title', '')}",
)


def _send_discord(ctx, args):
    from action_tools.discord_tool import send_alert
    sent = send_alert(
        title=args["title"],
        message=args["message"],
        severity=args.get("severity", "info"),
    )
    return {"sent": sent}


register_tool(
    name="send_discord",
    description="Post a message via Discord webhook. Falls back to desktop notification if unavailable.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["info", "warning", "critical", "success"], "default": "info"},
        },
        "required": ["title", "message"],
    },
    handler=_send_discord,
    summary_fn=lambda a: f"Discord post: {a.get('title', '')}",
)


def _send_email(ctx, args):
    """Send a plain email. Always requires approval (external-facing)."""
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    if not EMAIL_ENABLED:
        raise ValueError("Email not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD.")

    to = (args.get("to") or "").strip()
    subject = (args.get("subject") or "").strip()
    body = (args.get("body") or "").strip()
    if not to or not subject or not body:
        raise ValueError("to, subject, and body are all required")

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    # Auto-log as a CRM interaction if we can find a matching contact
    try:
        from api import crm as _crm
        for c in _crm.list_contacts(ctx["business_id"], search=to, limit=5):
            if (c.get("email") or "").strip().lower() == to.lower():
                _crm.create_interaction(ctx["business_id"], ctx["user_id"], {
                    "type": "email",
                    "subject": subject,
                    "summary": body[:500],
                    "contact_id": c["id"],
                    "company_id": c.get("company_id"),
                })
                break
    except Exception:
        pass

    return {"sent": True, "to": to, "subject": subject}


register_tool(
    name="send_email",
    description=(
        "Send an email to someone. Always requires approval. "
        "The agent should draft the subject and body for the user to review."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["to", "subject", "body"],
    },
    handler=_send_email,
    summary_fn=lambda a: f"EMAIL to {a.get('to')}: {a.get('subject', '')[:80]}",
)


def _push_notification(ctx, args):
    from api import notifications as _notifs
    nid = _notifs.push(
        title=args["title"],
        message=args.get("message", ""),
        severity=args.get("severity", "info"),
        type=args.get("type", "agent"),
        user_id=ctx["user_id"],
        business_id=ctx["business_id"],
    )
    return {"id": nid}


register_tool(
    name="push_notification",
    description=(
        "Create an in-app notification for the current business. Use sparingly — "
        "for things the user should see when they next open the app."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["info", "warning", "critical", "success"], "default": "info"},
            "type": {"type": "string", "default": "agent"},
        },
        "required": ["title"],
    },
    handler=_push_notification,
    summary_fn=lambda a: f"In-app notification: {a.get('title', '')[:80]}",
)
