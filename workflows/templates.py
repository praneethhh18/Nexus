"""
Pre-built workflow templates.
All ship with enabled=False — the user must explicitly enable them.
"""
from __future__ import annotations
from typing import List, Dict, Any


def _node(id: str, type: str, name: str, config: dict, x: float = 0, y: float = 0) -> dict:
    return {"id": id, "type": type, "name": name, "config": config, "x": x, "y": y}


def _edge(source: str, target: str, label: str = "") -> dict:
    return {"source": source, "target": target, "label": label}


# ── Template 1: Daily Sales Report ───────────────────────────────────────────
DAILY_SALES_REPORT: Dict[str, Any] = {
    "name": "Daily Sales Report",
    "description": "Every morning: query yesterday's sales, generate a PDF report, and save it.",
    "enabled": False,
    "tags": ["sales", "reporting", "scheduled"],
    "nodes": [
        _node("n1", "schedule_trigger", "Every Morning 08:00",
              {"mode": "daily", "daily_time": "08:00"}, 100, 100),
        _node("n2", "sql_query", "Yesterday's Sales",
              {"mode": "natural_language",
               "question": "Show total sales by product for yesterday",
               "max_rows": 50}, 350, 100),
        _node("n3", "summarize", "Summarize Sales",
              {"style": "executive", "max_points": 5}, 600, 100),
        _node("n4", "generate_report", "Build PDF Report",
              {"title": "Daily Sales Report", "include_chart": True, "chart_type": "bar"}, 850, 100),
        _node("n5", "save_file", "Save Report",
              {"filename_template": "daily_sales_{date}", "format": "txt"}, 1100, 100),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4"),
        _edge("n4", "n5"),
    ],
}


# ── Template 2: Anomaly Alert Pipeline ───────────────────────────────────────
ANOMALY_ALERT_PIPELINE: Dict[str, Any] = {
    "name": "Anomaly Alert Pipeline",
    "description": "Every hour: check sales metrics for anomalies, notify on Discord if found.",
    "enabled": False,
    "tags": ["anomaly", "alerts", "monitoring"],
    "nodes": [
        _node("n1", "schedule_trigger", "Hourly Check",
              {"mode": "interval", "interval_minutes": 60}, 100, 200),
        _node("n2", "sql_query", "Fetch Latest Metrics",
              {"mode": "natural_language",
               "question": "Show the latest sales metrics with region and revenue",
               "max_rows": 20}, 350, 200),
        _node("n3", "llm_condition", "Is There An Anomaly?",
              {"question": "Is there any anomalous or unusually low/high value in this data?",
               "true_label": "anomaly", "false_label": "normal"}, 600, 200),
        _node("n4", "summarize", "Describe Anomaly",
              {"style": "one_line", "max_points": 1}, 850, 150),
        _node("n5", "discord_notify", "Alert Discord",
              {"title": "Anomaly Detected — {workflow_name}",
               "message": "{input}", "severity": "high"}, 1100, 150),
        _node("n6", "desktop_notify", "Desktop Alert",
              {"title": "Anomaly!", "message": "{input}"}, 850, 350),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4", "anomaly"),
        _edge("n3", "n6", "normal"),
        _edge("n4", "n5"),
    ],
}


# ── Template 3: Weekly KPI Digest ─────────────────────────────────────────────
WEEKLY_KPI_DIGEST: Dict[str, Any] = {
    "name": "Weekly KPI Digest",
    "description": "Every Monday morning: pull KPIs, build a report, email it to the team.",
    "enabled": False,
    "tags": ["kpi", "weekly", "email", "reporting"],
    "nodes": [
        _node("n1", "schedule_trigger", "Monday 09:00",
              {"mode": "weekly", "weekly_day": "Monday", "weekly_time": "09:00"}, 100, 150),
        _node("n2", "sql_query", "Weekly Revenue",
              {"mode": "natural_language",
               "question": "Show total revenue, orders, and average order value for this week grouped by region",
               "max_rows": 20}, 350, 50),
        _node("n3", "sql_query", "Top Products",
              {"mode": "natural_language",
               "question": "Show top 5 products by revenue this week",
               "max_rows": 5}, 350, 250),
        _node("n4", "llm_prompt", "Draft KPI Summary",
              {"prompt": "Write a concise weekly KPI digest for executives based on this data:\n\n{input}",
               "max_words": 200}, 600, 150),
        _node("n5", "generate_report", "Build PDF",
              {"title": "Weekly KPI Digest", "include_chart": True, "chart_type": "auto"}, 850, 150),
        _node("n6", "send_email", "Email Team",
              {"to": "", "subject": "Weekly KPI Digest — {date}",
               "body_mode": "use_previous_output", "require_approval": True}, 1100, 150),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n1", "n3"),
        _edge("n2", "n4"),
        _edge("n3", "n4"),
        _edge("n4", "n5"),
        _edge("n5", "n6"),
    ],
}


# ── Template 4: Document Monitor & RAG Digest ────────────────────────────────
DOCUMENT_MONITOR: Dict[str, Any] = {
    "name": "Document Monitor & RAG Digest",
    "description": "Daily: search internal docs for a topic, summarize findings, save to file.",
    "enabled": False,
    "tags": ["rag", "documents", "knowledge"],
    "nodes": [
        _node("n1", "schedule_trigger", "Daily 07:00",
              {"mode": "daily", "daily_time": "07:00"}, 100, 150),
        _node("n2", "rag_search", "Search Policy Docs",
              {"query": "What are the key compliance and reporting requirements?",
               "top_k": 5}, 350, 150),
        _node("n3", "summarize", "Summarize Findings",
              {"style": "bullet_points", "max_points": 5}, 600, 150),
        _node("n4", "save_file", "Save Digest",
              {"filename_template": "doc_digest_{date}", "format": "txt"}, 850, 150),
        _node("n5", "desktop_notify", "Notify Ready",
              {"title": "Document Digest Ready",
               "message": "Today's doc digest has been saved."}, 1100, 150),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4"),
        _edge("n4", "n5"),
    ],
}


# ── Template 5: Revenue Drop Response ────────────────────────────────────────
REVENUE_DROP_RESPONSE: Dict[str, Any] = {
    "name": "Revenue Drop Response",
    "description": "Check if today's revenue dropped vs yesterday. If yes, alert and draft a response plan.",
    "enabled": False,
    "tags": ["revenue", "alerts", "ai-response"],
    "nodes": [
        _node("n1", "schedule_trigger", "Twice Daily",
              {"mode": "interval", "interval_minutes": 720}, 100, 200),
        _node("n2", "sql_query", "Revenue Comparison",
              {"mode": "natural_language",
               "question": "Compare today's total revenue vs yesterday's total revenue",
               "max_rows": 10}, 350, 200),
        _node("n3", "value_condition", "Revenue Dropped?",
              {"field": "output", "operator": "contains", "value": "drop",
               "true_label": "yes", "false_label": "no"}, 600, 200),
        _node("n4", "llm_prompt", "Draft Recovery Plan",
              {"prompt": "Based on this revenue data showing a drop:\n\n{input}\n\nSuggest 3 immediate actions to investigate and respond.",
               "max_words": 300}, 850, 100),
        _node("n5", "discord_notify", "Alert: Revenue Drop",
              {"title": "Revenue Drop Alert",
               "message": "{input}", "severity": "high"}, 1100, 100),
        _node("n6", "save_file", "Log Revenue Data",
              {"filename_template": "revenue_check_{date}_{time}", "format": "txt"}, 850, 350),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4", "yes"),
        _edge("n3", "n6", "no"),
        _edge("n4", "n5"),
    ],
}


TEMPLATES: List[Dict[str, Any]] = [
    DAILY_SALES_REPORT,
    ANOMALY_ALERT_PIPELINE,
    WEEKLY_KPI_DIGEST,
    DOCUMENT_MONITOR,
    REVENUE_DROP_RESPONSE,
]


def get_all_templates() -> List[Dict[str, Any]]:
    """Return all template definitions (deep copies — safe to mutate)."""
    import copy
    return copy.deepcopy(TEMPLATES)


def get_template_by_name(name: str) -> Dict[str, Any] | None:
    import copy
    for t in TEMPLATES:
        if t["name"] == name:
            return copy.deepcopy(t)
    return None
