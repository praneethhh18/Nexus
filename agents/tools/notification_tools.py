"""Notification + email tools for the agent."""
from __future__ import annotations

from loguru import logger

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
    """Send a plain email. Always requires approval (external-facing).
    Uses api.email_provider — picks Resend if configured, else Gmail SMTP."""
    from api import email_provider as _ep
    if not _ep.is_configured():
        raise ValueError(
            "Email not configured. Set RESEND_API_KEY (recommended) or "
            "GMAIL_USER + GMAIL_APP_PASSWORD in .env."
        )

    to = (args.get("to") or "").strip()
    subject = (args.get("subject") or "").strip()
    body = (args.get("body") or "").strip()
    if not to or not subject or not body:
        raise ValueError("to, subject, and body are all required")
    # Reject placeholder stubs the LLM sometimes ships instead of real
    # content. Without this we ended up with approval rows containing
    # body='(body)' that the user couldn't sensibly approve.
    _placeholders = {
        "(body)", "(subject)", "(content)", "(message)",
        "body", "subject", "content", "tbd", "todo", "to be filled",
        "<body>", "<subject>", "{body}", "{subject}", "...", "…",
    }
    if subject.lower() in _placeholders or len(subject) < 5:
        raise ValueError(
            "Subject is too short or a placeholder. Write the actual "
            "email subject before queuing."
        )
    if body.lower() in _placeholders or len(body) < 20:
        raise ValueError(
            "Body is empty or a placeholder. Write the actual email "
            "content (greeting + 1-3 sentences + sign-off) before "
            "calling send_email."
        )

    # Anti-hallucination guard for the recipient address. The LLM has
    # been observed inventing addresses like 'praneeth.pk@example.com'
    # by mashing the contact's name with a placeholder domain, instead
    # of calling find_contacts to read the real CRM email
    # (praneethhh0218@gmail.com in the case that triggered this guard).
    # Two checks:
    #   1. Reject well-known placeholder / example domains outright.
    #   2. Soft-warn (but ALLOW) any email that's neither in the CRM nor
    #      in the user's most recent message — the agent had no source
    #      for it, but we can't assume every cold outreach is wrong.
    _PLACEHOLDER_DOMAINS = {
        "example.com", "example.org", "example.net",
        "test.com", "test.org",
        "placeholder.com", "placeholder.org",
        "sample.com", "sample.org",
        "demo.com", "demo.org",
        "yourdomain.com", "yourcompany.com",
        "domain.com", "company.com",
        "email.com",
        "localhost",
    }
    if "@" not in to:
        raise ValueError(
            f"'{to}' doesn't look like an email address. Look up the "
            f"recipient with find_contacts first to get their real email."
        )
    domain = to.rsplit("@", 1)[-1].lower().strip()
    if domain in _PLACEHOLDER_DOMAINS:
        raise ValueError(
            f"'{to}' uses a placeholder domain ({domain}). This is the "
            f"sign of a fabricated email. Call find_contacts to look up "
            f"the recipient's REAL email from the CRM, or ask the user "
            f"for the correct address — do not guess."
        )

    result = _ep.send_email(to=to, subject=subject, body=body)

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
    except Exception as e:
        # Email already sent — failing to log it as a CRM interaction shouldn't block.
        logger.warning(f"[NotificationTools] CRM interaction log failed for {to}: {e}")

    return {"sent": True, "to": to, "subject": subject,
            "provider": result.get("provider"), "id": result.get("id", "")}


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
