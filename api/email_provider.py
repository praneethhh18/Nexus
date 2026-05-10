"""Single email-sending abstraction — picks Resend if configured, else Gmail SMTP.

Why an abstraction:
    Before this, 3 different agent tools (notification_tools, email_template_tools,
    outreach_tools) each contained their own smtplib.SMTP block. Switching email
    providers meant changing 3 places + risking inconsistencies.

How provider selection works:
    1. RESEND_API_KEY set       → use Resend (3K/mo free, professional, tracked)
    2. GMAIL_USER + APP_PASSWORD → fall back to Gmail SMTP (500/day Gmail cap)
    3. Neither                   → raises a clear error at send time

Resend caveat:
    Until you verify a custom domain at resend.com, the sender MUST be a
    resend.dev address (e.g. onboarding@resend.dev). After domain verification
    you can set EMAIL_FROM=hi@nexusagent.in and emails will land with proper
    DKIM/SPF, no spam folder issues.
"""
from __future__ import annotations

import os
from typing import Optional

from loguru import logger


def _provider() -> str:
    """Resolve which provider to use this call. Order: Resend → Gmail SMTP."""
    if (os.getenv("RESEND_API_KEY") or "").strip():
        return "resend"
    if (os.getenv("GMAIL_USER") or "").strip() and (os.getenv("GMAIL_APP_PASSWORD") or "").strip():
        return "gmail_smtp"
    return "none"


def is_configured() -> bool:
    """True if any email backend is wired up. Used by health checks + the
    send_email tool's pre-flight to give a friendlier error than smtplib's."""
    return _provider() != "none"


def default_from() -> str:
    """Resolve the From address. Resend requires this be either:
        - a verified domain (e.g. hi@nexusagent.in after DNS setup), OR
        - any *@resend.dev address (works without domain verification)
    Gmail SMTP just uses GMAIL_USER directly."""
    if _provider() == "resend":
        return (os.getenv("EMAIL_FROM") or "onboarding@resend.dev").strip()
    return (os.getenv("GMAIL_USER") or "").strip()


def send_email(*, to: str, subject: str, body: str,
                from_addr: Optional[str] = None,
                reply_to: Optional[str] = None) -> dict:
    """Send one transactional email. Returns {'ok': True, 'id': str, 'provider': str}.

    Raises RuntimeError on any failure — callers should catch + show the user.
    """
    to = (to or "").strip()
    subject = (subject or "").strip()
    body = (body or "").strip()
    if not to or not subject or not body:
        raise ValueError("to, subject, and body are all required")

    sender = (from_addr or default_from()).strip()
    if not sender:
        raise RuntimeError(
            "No email provider configured — set either RESEND_API_KEY or "
            "GMAIL_USER + GMAIL_APP_PASSWORD in .env."
        )

    provider = _provider()
    if provider == "resend":
        return _send_via_resend(sender=sender, to=to, subject=subject,
                                 body=body, reply_to=reply_to)
    if provider == "gmail_smtp":
        return _send_via_gmail_smtp(sender=sender, to=to, subject=subject,
                                     body=body, reply_to=reply_to)
    raise RuntimeError(
        "No email provider configured — set either RESEND_API_KEY or "
        "GMAIL_USER + GMAIL_APP_PASSWORD in .env."
    )


# ── Resend backend ─────────────────────────────────────────────────────────
def _send_via_resend(*, sender: str, to: str, subject: str, body: str,
                      reply_to: Optional[str]) -> dict:
    """Call Resend's REST API directly via httpx. Avoids needing the resend
    SDK — keeps the dep surface tight."""
    import httpx

    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("RESEND_API_KEY missing")

    payload = {
        "from":    sender,
        "to":      [to],
        "subject": subject,
        "text":    body,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type":  "application/json",
                },
                json=payload,
            )
    except Exception as e:
        raise RuntimeError(f"Resend network error: {e}")

    if r.status_code not in (200, 201, 202):
        # Resend returns useful error JSON — bubble it up so the user sees
        # "domain not verified" / "invalid From address" / "rate limited" etc.
        try:
            err = r.json().get("message") or r.json().get("error") or r.text[:200]
        except Exception:
            err = r.text[:200]
        raise RuntimeError(f"Resend HTTP {r.status_code}: {err}")

    data = r.json()
    msg_id = data.get("id", "")
    logger.info(f"[email] resend ok id={msg_id} to={to} from={sender}")
    return {"ok": True, "id": msg_id, "provider": "resend"}


# ── Gmail SMTP backend ─────────────────────────────────────────────────────
def _send_via_gmail_smtp(*, sender: str, to: str, subject: str, body: str,
                          reply_to: Optional[str]) -> dict:
    """Fallback. Uses smtplib over Gmail's submission server. 500/day cap."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    password = (os.getenv("GMAIL_APP_PASSWORD") or "").strip()
    if not password:
        raise RuntimeError("GMAIL_APP_PASSWORD missing")

    msg = MIMEMultipart()
    msg["From"]    = sender
    msg["To"]      = to
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
    except Exception as e:
        raise RuntimeError(f"Gmail SMTP error: {e}")

    logger.info(f"[email] gmail_smtp ok to={to} from={sender}")
    return {"ok": True, "id": "", "provider": "gmail_smtp"}
