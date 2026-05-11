"""Transactional emails for the signup → email-verification → trial flow.

The verify link gates the 14-day Pro trial. Until the user clicks the link
in this email, their account exists but the trial subscription row does NOT
exist (plan_gate falls back to 'free').

Failures here MUST NEVER raise — log loud, return False. A signup that can't
send the verification email should still create the account; the resend
endpoint lets the user retry from the post-signup screen.
"""
from __future__ import annotations

import os

from loguru import logger

from api.email_provider import send_email, is_configured


def _app_url() -> str:
    return (os.getenv("APP_BASE_URL") or "https://app.nexusagent.in").rstrip("/")


def _support_email() -> str:
    return os.getenv("SUPPORT_EMAIL") or "hi@nexusagent.in"


def send_verification_email(*, to_email: str, name: str, token: str) -> bool:
    """Send the one-time verify link. Returns True on success.

    The verify URL is ALWAYS logged to the terminal (loud banner) regardless
    of whether the actual email send succeeds. This is the escape hatch for:
      - Dev environments with no SMTP wired
      - Resend configured but domain not yet DNS-verified (send returns 4xx)
      - Customer's mail server rejected the message (greylisting etc.)
    Without this banner the user would be stuck — account created, no way in.
    """
    verify_url = f"{_app_url()}/verify-email?token={token}"

    # Always log first so you can copy from terminal even if send fails below.
    logger.info(
        "\n"
        "================================================================\n"
        f"  VERIFY-EMAIL link for {to_email}\n"
        f"  {verify_url}\n"
        f"  Valid 48h. Paste into your browser if the email doesn't arrive.\n"
        "================================================================"
    )

    if not is_configured():
        logger.warning("[verification] No SMTP configured — only the terminal link is available.")
        return False

    first_name = (name or "").split(" ")[0] or "there"
    subject = "Verify your email to start your NexusAgent Pro trial"

    text_body = (
        f"Hi {first_name},\n\n"
        f"Welcome to NexusAgent! Click the link below to verify your email "
        f"and unlock your 14-day Pro trial — full access to all 8 AI agents, "
        f"no credit card needed.\n\n"
        f"  {verify_url}\n\n"
        f"This link is valid for 48 hours. After verification you'll land on "
        f"your dashboard with the trial active.\n\n"
        f"If you didn't sign up for NexusAgent, just ignore this email — your "
        f"address won't be used for anything else.\n\n"
        f"— The NexusAgent team\n"
        f"{_support_email()}\n"
    )

    html_body = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f6f7fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a2e;">
  <div style="max-width:560px;margin:32px auto;padding:0 16px;">
    <div style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
      <div style="background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);padding:28px 32px;color:#fff;">
        <div style="font-size:11px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;opacity:0.9;">One last step</div>
        <h1 style="margin:6px 0 0;font-size:24px;font-weight:700;letter-spacing:-0.01em;">Verify your email to start your trial</h1>
      </div>
      <div style="padding:28px 32px;">
        <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Hi {first_name},</p>
        <p style="margin:0 0 22px;font-size:15px;line-height:1.6;">
          Welcome to NexusAgent! Click the button below to verify your email and
          unlock your <strong>14-day Pro trial</strong> — full access to all 8 AI
          agents, no credit card needed.
        </p>
        <p style="margin:0 0 22px;text-align:center;">
          <a href="{verify_url}"
             style="display:inline-block;background:#6366F1;color:#fff;
                    text-decoration:none;padding:13px 28px;border-radius:10px;
                    font-weight:600;font-size:15px;">
            Verify email and start trial
          </a>
        </p>
        <p style="margin:0 0 8px;font-size:13px;color:#666;line-height:1.6;">
          Or paste this link into your browser:
        </p>
        <p style="margin:0 0 22px;font-size:12px;word-break:break-all;color:#6366F1;">
          {verify_url}
        </p>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0;"/>
        <p style="margin:0;font-size:12.5px;color:#888;line-height:1.6;">
          This link is valid for 48 hours. If you didn't sign up for NexusAgent,
          just ignore this email — your address won't be used for anything else.
        </p>
      </div>
    </div>
    <p style="text-align:center;margin:18px 0 0;font-size:12px;color:#999;">
      Need help? Reply to this email — {_support_email()}
    </p>
  </div>
</body></html>"""

    try:
        send_email(
            to=to_email,
            subject=subject,
            body=text_body,
            html_body=html_body,
        )
        logger.info(f"[verification] sent to={to_email}")
        return True
    except Exception as e:
        logger.error(f"[verification] failed to send to={to_email}: {e}")
        return False
