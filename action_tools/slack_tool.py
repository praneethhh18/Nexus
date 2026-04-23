"""
Slack notification tool — sends messages via incoming webhook.

Slack doesn't ship an "embed" format like Discord, so we use Block Kit for
rich formatting. Falls back silently if SLACK_WEBHOOK_URL isn't configured —
higher-level code should prefer this tool when the business uses Slack.
"""
from __future__ import annotations

import time
from datetime import datetime

from loguru import logger

from config.settings import SLACK_WEBHOOK_URL, SLACK_ENABLED

SEVERITY_EMOJI = {
    "info": ":information_source:",
    "warning": ":warning:",
    "critical": ":rotating_light:",
    "success": ":white_check_mark:",
}

SEVERITY_COLOR = {
    "info": "#3498DB",
    "warning": "#F39C12",
    "critical": "#E74C3C",
    "success": "#2ECC71",
}


def _validate_webhook_url(url: str) -> bool:
    return url.startswith("https://hooks.slack.com/services/")


def _send_slack(title: str, message: str, severity: str = "info") -> bool:
    if not _validate_webhook_url(SLACK_WEBHOOK_URL):
        logger.warning("[Slack] Invalid webhook URL format")
        return False
    try:
        import requests
        emoji = SEVERITY_EMOJI.get(severity, ":bell:")
        color = SEVERITY_COLOR.get(severity, "#3498DB")
        payload = {
            "attachments": [{
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"{emoji} {title}"},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message[:2900]},
                    },
                    {
                        "type": "context",
                        "elements": [{
                            "type": "mrkdwn",
                            "text": f"NexusAgent · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        }],
                    },
                ],
            }]
        }
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code in (200, 204):
            logger.success(f"[Slack] Sent: {title}")
            return True
        logger.warning(f"[Slack] HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"[Slack] Send failed: {e}")
        return False


def send_alert(
    title: str,
    message: str,
    severity: str = "info",
    business_id: str = "default",
    user_id: str = "default",
) -> bool:
    """Send an alert to Slack. severity: info | warning | critical | success"""
    start = time.time()

    icon = {"info": "[i]", "warning": "[!]", "critical": "[!!]", "success": "[ok]"}.get(severity, "[*]")
    try:
        print(f"\n{icon} [SLACK {severity.upper()}] {title}\n   {message}\n")
    except UnicodeEncodeError:
        print(f"\n[SLACK {severity.upper()}] {title}\n   {message}\n")

    sent = _send_slack(title, message, severity) if SLACK_ENABLED else False
    duration_ms = int((time.time() - start) * 1000)

    try:
        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="slack_tool",
            input_summary=f"{severity}: {title}",
            output_summary=f"sent={sent}",
            duration_ms=duration_ms,
            approved=True,
            success=sent,
            business_id=business_id,
            user_id=user_id,
        )
    except Exception:
        pass

    return sent
