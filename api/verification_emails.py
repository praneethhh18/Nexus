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


def send_trial_welcome_email(*, to_email: str, name: str, business_name: str | None = None) -> bool:
    """Send the post-verification 'your trial is live' email.

    Fires from /api/auth/verify-email AFTER the trial has been activated so
    the customer's first inbox touchpoint is celebratory + actionable, not
    just a verification receipt. Includes:
      - confirmation the trial is running + expiry date (14 days)
      - 3 quick-start nudges (Atlas / Vox / templates)
      - a one-click feedback mailto so we capture friction early
      - link back to the dashboard

    Never raises: failures here must not block the verify-email response
    (the trial is already active in the DB; an email retry can come later
    via a separate flow).
    """
    from datetime import datetime, timedelta, timezone
    first_name = (name or "").split(" ")[0] or "there"
    biz = business_name or "your workspace"
    expires_on = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%d %b %Y")
    dashboard_url = _app_url()
    support = _support_email()
    feedback_mailto = (
        f"mailto:{support}?subject=NexusAgent%20trial%20feedback%20-%20{first_name}"
        f"&body=Hi%20team%2C%0A%0AHere%27s%20my%20feedback%20after%20trying%20NexusAgent%3A%0A%0A"
    )

    logger.info(f"[welcome] preparing trial-welcome for {to_email} (biz={biz}, expires={expires_on})")

    if not is_configured():
        logger.warning("[welcome] No SMTP configured — skipping trial-welcome email.")
        return False

    subject = f"Your NexusAgent Pro trial is live, {first_name} 🎉"

    text_body = (
        f"Hi {first_name},\n\n"
        f"Your 14-day Pro trial for {biz} is now active. All 8 AI agents are unlocked "
        f"until {expires_on} — no card on file, no surprise charges.\n\n"
        f"Three things to try in the next 10 minutes:\n"
        f"  1. Open the dashboard and let Atlas import your contacts from a CSV.\n"
        f"  2. Ask Vox to draft your first outbound voice call script.\n"
        f"  3. Browse the industry-tuned email templates Inbox set up for you.\n\n"
        f"Dashboard: {dashboard_url}\n\n"
        f"We're a tiny team building this for Indian SMBs, and your first impressions "
        f"matter to us more than almost anything else. If something feels off, slow, or "
        f"missing, please reply to this email — it lands directly with the founders.\n\n"
        f"On day 11 you'll get a heads-up about choosing a plan. Until then, just use it.\n\n"
        f"— The NexusAgent team\n"
        f"{support}\n"
    )

    html_body = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f6f7fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a2e;">
  <div style="max-width:560px;margin:32px auto;padding:0 16px;">
    <div style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
      <div style="background:linear-gradient(135deg,#10b981 0%,#6366F1 60%,#8B5CF6 100%);padding:32px;color:#fff;">
        <div style="font-size:11px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;opacity:0.9;">Your trial is live</div>
        <h1 style="margin:6px 0 0;font-size:26px;font-weight:700;letter-spacing:-0.01em;">
          Welcome to NexusAgent, {first_name} 🎉
        </h1>
        <p style="margin:10px 0 0;font-size:14px;opacity:0.92;line-height:1.5;">
          All 8 AI agents unlocked for <strong>{biz}</strong> · expires {expires_on} · no card on file
        </p>
      </div>
      <div style="padding:28px 32px;">
        <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">
          You're in. Here are three things worth doing in the next 10 minutes:
        </p>
        <ol style="margin:0 0 22px;padding-left:22px;font-size:14.5px;line-height:1.7;color:#333;">
          <li><strong>Open the dashboard</strong> and let <strong>Atlas</strong> import your contacts from a CSV.</li>
          <li>Ask <strong>Vox</strong> to draft your first outbound voice call script.</li>
          <li>Browse the industry-tuned email templates <strong>Inbox</strong> set up for you.</li>
        </ol>
        <p style="margin:0 0 22px;text-align:center;">
          <a href="{dashboard_url}"
             style="display:inline-block;background:#6366F1;color:#fff;
                    text-decoration:none;padding:13px 28px;border-radius:10px;
                    font-weight:600;font-size:15px;">
            Open my dashboard
          </a>
        </p>
        <div style="background:#f6f7fb;border-radius:12px;padding:18px 20px;margin:24px 0;">
          <p style="margin:0 0 8px;font-size:13.5px;font-weight:600;color:#1a1a2e;">
            One favour 🙏
          </p>
          <p style="margin:0;font-size:13px;line-height:1.6;color:#555;">
            We're a tiny team building this for Indian SMBs and your first impressions
            matter more than almost anything else. If something feels off, slow, or
            missing — <a href="{feedback_mailto}" style="color:#6366F1;text-decoration:none;font-weight:600;">tell us in two lines</a>.
            It lands directly with the founders.
          </p>
        </div>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0;"/>
        <p style="margin:0;font-size:12.5px;color:#888;line-height:1.6;">
          On day 11 we'll send a heads-up about choosing a plan. Until then, just use it.
          Reply to this email any time — it goes straight to {support}.
        </p>
      </div>
    </div>
    <p style="text-align:center;margin:18px 0 0;font-size:12px;color:#999;">
      NexusAgent · Built for Indian SMBs
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
        logger.info(f"[welcome] trial-welcome sent to={to_email}")
        return True
    except Exception as e:
        logger.error(f"[welcome] failed to send trial-welcome to={to_email}: {e}")
        return False
