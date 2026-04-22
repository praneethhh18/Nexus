"""
Trigger node implementations.
Triggers always run first and return initial context data.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any


def run_schedule_trigger(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["trigger_data"] = {
        "type": "schedule",
        "fired_at": datetime.now().isoformat(),
        "mode": config.get("mode", "daily"),
    }
    ctx["output"] = f"Scheduled trigger fired at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return ctx


def run_manual_trigger(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["trigger_data"] = {
        "type": "manual",
        "fired_at": datetime.now().isoformat(),
    }
    ctx["output"] = f"Manual trigger activated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return ctx


def run_anomaly_trigger(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Runs anomaly detection and injects results into context."""
    try:
        from orchestrator.proactive_monitor import check_anomalies
        threshold = config.get("threshold_pct", 15) / 100
        watch_regions = config.get("regions", [])

        result = check_anomalies()
        anomalies = result.get("anomalies_found", [])

        if watch_regions:
            anomalies = [a for a in anomalies if a["region"] in watch_regions]

        ctx["trigger_data"] = {
            "type": "anomaly",
            "anomalies": anomalies,
            "fired_at": datetime.now().isoformat(),
        }
        if anomalies:
            lines = [f"{a['region']}: {a['drop_pct']:.1f}% drop" for a in anomalies]
            ctx["output"] = "Anomalies detected:\n" + "\n".join(lines)
        else:
            ctx["output"] = "No anomalies detected"
            ctx["_skip"] = True   # Skip rest of workflow if no anomalies

    except Exception as e:
        ctx["output"] = f"Anomaly check failed: {e}"
        ctx["_skip"] = True

    return ctx


def run_webhook_trigger(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["trigger_data"] = {
        "type": "webhook",
        "path": config.get("path", "/webhook"),
        "fired_at": datetime.now().isoformat(),
    }
    ctx["output"] = ctx.get("_webhook_payload", "Webhook received")
    return ctx
