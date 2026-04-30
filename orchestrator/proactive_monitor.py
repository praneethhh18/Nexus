"""
Proactive Monitor — background APScheduler job that detects anomalies in sales data.
Sends alerts without being asked.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import pandas as pd
from loguru import logger

from config.settings import ANOMALY_THRESHOLD, MONITOR_INTERVAL_MINUTES

_scheduler = None
_last_check_result: Dict[str, Any] = {}
_scheduler_lock = threading.Lock()


def check_anomalies() -> Dict[str, Any]:
    """
    Query sales_metrics, compute 7-day rolling averages, detect drops > ANOMALY_THRESHOLD.
    Generates alerts and PDF report for each anomaly found.
    """
    from pathlib import Path
    from config.db import get_conn

    result = {
        "checked_at": datetime.now().isoformat(),
        "anomalies_found": [],
        "regions_checked": [],
        "error": None,
    }

    if not Path(DB_PATH).exists():
        result["error"] = "Database not found"
        return result

    try:
        import sqlite3
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT date, region, revenue FROM sales_metrics WHERE metric_type='daily' ORDER BY date",
            conn
        )
        conn.close()

        if df.empty:
            result["error"] = "No data in sales_metrics"
            return result

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        result["regions_checked"] = df["region"].unique().tolist()

        cutoff = df["date"].max() - timedelta(days=30)
        recent_df = df[df["date"] >= cutoff]

        anomalies = []
        for region, group in recent_df.groupby("region"):
            group = group.sort_values("date").copy()
            group["rolling_avg"] = group["revenue"].rolling(window=7, min_periods=3).mean()
            group = group.dropna(subset=["rolling_avg"])

            if group.empty:
                continue

            latest = group.iloc[-1]
            avg = latest["rolling_avg"]
            rev = latest["revenue"]

            if avg > 0:
                drop_pct = (avg - rev) / avg
                if drop_pct > ANOMALY_THRESHOLD:
                    anomaly = {
                        "region": region,
                        "date": str(latest["date"].date()),
                        "revenue": round(rev, 2),
                        "rolling_avg": round(avg, 2),
                        "drop_pct": round(drop_pct * 100, 1),
                    }
                    anomalies.append(anomaly)
                    logger.warning(
                        f"[Monitor] ANOMALY: {region} — revenue {rev:.0f} "
                        f"vs avg {avg:.0f} ({drop_pct:.0%} drop)"
                    )

        result["anomalies_found"] = anomalies

        if anomalies:
            _handle_anomalies(anomalies)

        _last_check_result.update(result)
        logger.info(f"[Monitor] Check complete: {len(anomalies)} anomalies found")
        return result

    except Exception as e:
        logger.error(f"[Monitor] check_anomalies error: {e}")
        result["error"] = str(e)
        return result


def _handle_anomalies(anomalies: List[Dict[str, Any]]) -> None:
    """Generate report and send alerts for detected anomalies."""
    from action_tools.discord_tool import send_alert
    from voice.speaker import speak_alert

    for anomaly in anomalies:
        region = anomaly["region"]
        drop = anomaly["drop_pct"]
        rev = anomaly["revenue"]

        title = f"Revenue Anomaly: {region} Region"
        message = (
            f"Revenue dropped {drop}% below 7-day average.\n"
            f"Current: ${rev:,.0f}  |  Average: ${anomaly['rolling_avg']:,.0f}\n"
            f"Date: {anomaly['date']}"
        )

        severity = "critical" if drop > 30 else "warning"
        send_alert(title, message, severity)

        try:
            speak_alert(f"Alert! {region} region revenue dropped {drop:.0f} percent below average.")
        except Exception:
            pass

        # Generate PDF report for each anomaly
        try:
            _generate_anomaly_report(anomaly)
        except Exception as e:
            logger.warning(f"[Monitor] Report generation failed: {e}")

    try:
        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="proactive_monitor",
            input_summary="scheduled anomaly check",
            output_summary=f"{len(anomalies)} anomalies found",
            duration_ms=0,
            approved=True,
            success=True,
        )
    except Exception:
        pass


def _generate_anomaly_report(anomaly: Dict[str, Any]) -> Optional[str]:
    """Generate a PDF report for a single anomaly."""
    try:
        import sqlite3
        import pandas as pd
        from config.db import get_conn
        from report_generator.chart_builder import build_chart
        from report_generator.pdf_builder import build_pdf

        region = anomaly["region"]
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT date, revenue FROM sales_metrics WHERE region=? AND metric_type='daily' ORDER BY date DESC LIMIT 30",
            conn, params=(region,)
        )
        conn.close()

        df = df.sort_values("date")
        _, png_path = build_chart(df, "line", f"{region} Revenue — Last 30 Days")

        summary = (
            f"Automated anomaly detection has identified a significant revenue drop "
            f"in the {region} region. Revenue fell to ${anomaly['revenue']:,.0f}, "
            f"which is {anomaly['drop_pct']:.1f}% below the 7-day rolling average of "
            f"${anomaly['rolling_avg']:,.0f}. Immediate investigation is recommended."
        )

        insights = [
            f"Region: {region}",
            f"Revenue drop: {anomaly['drop_pct']:.1f}%",
            f"Current revenue: ${anomaly['revenue']:,.0f}",
            f"7-day avg: ${anomaly['rolling_avg']:,.0f}",
            "Action required: Review sales pipeline and regional performance",
        ]

        pdf_path = build_pdf(
            title=f"Anomaly Alert: {region} Region",
            executive_summary=summary,
            dataframe=df,
            chart_image_path=png_path,
            key_insights=insights,
        )
        from action_tools.discord_tool import send_report_ready
        send_report_ready(pdf_path)
        return pdf_path
    except Exception as e:
        logger.error(f"[Monitor] Report generation error: {e}")
        return None


def manual_trigger() -> Dict[str, Any]:
    """Manually trigger the anomaly check (used from UI)."""
    logger.info("[Monitor] Manual trigger initiated.")
    return check_anomalies()


def get_last_check_status() -> Dict[str, Any]:
    """Return the result of the most recent check."""
    return _last_check_result or {"status": "No checks run yet"}


def start_scheduler() -> bool:
    """Start the background APScheduler job."""
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None:
            return True
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            _scheduler = BackgroundScheduler()
            _scheduler.add_job(
                check_anomalies,
                "interval",
                minutes=MONITOR_INTERVAL_MINUTES,
                id="anomaly_check",
                replace_existing=True,
            )
            _scheduler.start()
            logger.success(
                f"[Monitor] Scheduler started — checking every {MONITOR_INTERVAL_MINUTES} min."
            )
            return True
        except Exception as e:
            logger.error(f"[Monitor] Scheduler start failed: {e}")
            return False


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None:
            try:
                _scheduler.shutdown(wait=False)
                logger.info("[Monitor] Scheduler stopped.")
            except Exception:
                pass
            _scheduler = None
