"""
Proactive alerts panel component with improved styling.
"""
from __future__ import annotations

import streamlit as st


SEVERITY_COLOR = {
    "critical": "#ef4444",
    "warning": "#f59e0b",
    "info": "#3b82f6",
    "success": "#22c55e",
}

SEVERITY_ICON = {
    "critical": "!!",
    "warning": "!",
    "info": "i",
    "success": "OK",
}


def render_alerts_panel(alert_history: list[dict]) -> None:
    """Render the alerts tab."""
    if not alert_history:
        st.info("No alerts yet. The proactive monitor will alert you when anomalies are detected.")
        return

    st.caption(f"{len(alert_history)} alert(s) since session started")

    for alert in reversed(alert_history[-20:]):
        severity = alert.get("severity", "info")
        color = SEVERITY_COLOR.get(severity, "#3b82f6")
        icon = SEVERITY_ICON.get(severity, "i")
        title = alert.get("title", "Alert")
        message = alert.get("message", "")
        ts = alert.get("timestamp", "")

        st.markdown(
            f'<div class="alert-item alert-{severity}" '
            f'style="border-left-color:{color};">'
            f'<div style="font-weight:600;font-size:13px;color:{color};">'
            f'[{icon}] {title}</div>'
            f'<div style="font-size:12px;margin-top:4px;color:#e2e8f0;">{message}</div>'
            f'<div style="font-size:10px;color:#64748b;margin-top:4px;">{ts}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
