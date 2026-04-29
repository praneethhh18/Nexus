"""
Discord notification tool — sends rich embeds via webhook.
Falls back to desktop notifications (plyer) + console if Discord not configured.
"""
from __future__ import annotations

import time
from datetime import datetime

from loguru import logger

from config.settings import DISCORD_WEBHOOK_URL, DISCORD_ENABLED

SEVERITY_COLORS = {
    "info": 0x3498DB,      # blue
    "warning": 0xF39C12,   # yellow
    "critical": 0xE74C3C,  # red
    "success": 0x2ECC71,   # green
}


def _validate_webhook_url(url: str) -> bool:
    """Basic validation that the URL looks like a Discord webhook."""
    return (
        url.startswith("https://discord.com/api/webhooks/")
        or url.startswith("https://discordapp.com/api/webhooks/")
    )


def _send_discord(title: str, message: str, severity: str = "info") -> bool:
    """Send a Discord embed via webhook."""
    if not _validate_webhook_url(DISCORD_WEBHOOK_URL):
        logger.warning("[Discord] Invalid webhook URL format")
        return False
    try:
        import requests
        color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["info"])
        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": color,
                "footer": {"text": f"NexusAgent • {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
                "timestamp": datetime.utcnow().isoformat(),
            }]
        }
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code in (200, 204):
            logger.success(f"[Discord] Sent: {title}")
            return True
        logger.warning(f"[Discord] HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"[Discord] Send failed: {e}")
        return False


def _send_desktop(title: str, message: str, severity: str = "info") -> bool:
    """Fallback: desktop notification via plyer."""
    try:
        from plyer import notification
        notification.notify(
            title=f"NexusAgent [{severity.upper()}] {title}",
            message=message[:256],
            timeout=8,
        )
        logger.info(f"[Notify] Desktop notification sent: {title}")
        return True
    except Exception as e:
        logger.warning(f"[Notify] Desktop notify unavailable: {e}")
        return False


def send_alert(
    title: str,
    message: str,
    severity: str = "info",
) -> bool:
    """
    Send an alert via Discord webhook (if configured) or desktop notification.
    severity: info | warning | critical | success
    """
    start = time.time()

    # Always print to console clearly (use ASCII-safe icons for Windows console)
    icon = {"info": "[i]", "warning": "[!]", "critical": "[!!]", "success": "[ok]"}.get(severity, "[*]")
    try:
        print(f"\n{icon} [{severity.upper()}] {title}\n   {message}\n")
    except UnicodeEncodeError:
        print(f"\n[{severity.upper()}] {title}\n   {message}\n")

    sent = False
    if DISCORD_ENABLED:
        sent = _send_discord(title, message, severity)
    else:
        sent = _send_desktop(title, message, severity)

    duration_ms = int((time.time() - start) * 1000)

    try:
        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="discord_tool",
            input_summary=f"{severity}: {title}",
            output_summary=f"sent={sent}",
            duration_ms=duration_ms,
            approved=True,
            success=sent,
        )
    except Exception:
        pass

    return sent


def send_report_ready(report_path: str) -> bool:
    """Notify that a PDF report has been generated."""
    from pathlib import Path
    filename = Path(report_path).name
    return send_alert(
        title="Report Ready",
        message=f"PDF report generated: {filename}\nPath: {report_path}",
        severity="success",
    )
