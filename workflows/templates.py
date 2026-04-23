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


# ── Template 6: Auto Email Sender ───────────────────────────────────────────
AUTO_EMAIL_SENDER: Dict[str, Any] = {
    "name": "Auto Email Sender",
    "description": "Query data, have AI draft a professional email, review and send to a recipient.",
    "enabled": False,
    "tags": ["email", "communication", "ai-draft"],
    "nodes": [
        _node("n1", "manual_trigger", "Start Email Flow",
              {"label": "Compose Email"}, 100, 200),
        _node("n2", "sql_query", "Gather Context Data",
              {"mode": "natural_language",
               "question": "Show summary of key metrics: total revenue, top region, order count for this month",
               "max_rows": 10}, 350, 200),
        _node("n3", "llm_prompt", "Draft Email",
              {"prompt": "Write a professional business email to the team summarizing these key metrics:\n\n{input}\n\nMake it concise, highlight wins and concerns. Sign off as NexusAgent.",
               "max_words": 250}, 600, 200),
        _node("n4", "send_email", "Send to Team",
              {"to": "", "subject": "Monthly Business Update — {date}",
               "body_mode": "use_previous_output", "require_approval": True}, 900, 200),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4"),
    ],
}

# ── Template 7: Meeting Scheduler ────────────────────────────────────────────
MEETING_SCHEDULER: Dict[str, Any] = {
    "name": "Meeting Scheduler",
    "description": "AI analyzes data to identify issues, drafts a meeting agenda, and sends a calendar invite email.",
    "enabled": False,
    "tags": ["meeting", "scheduling", "email", "ai"],
    "nodes": [
        _node("n1", "schedule_trigger", "Weekly Monday 08:30",
              {"mode": "weekly", "weekly_day": "Monday", "weekly_time": "08:30"}, 100, 200),
        _node("n2", "sql_query", "Pull Week's Data",
              {"mode": "natural_language",
               "question": "Show revenue by region, top issues, and any anomalies from the past 7 days",
               "max_rows": 20}, 350, 200),
        _node("n3", "llm_prompt", "Generate Meeting Agenda",
              {"prompt": "Based on this week's business data:\n\n{input}\n\nCreate a structured meeting agenda with:\n1. Key metrics review\n2. Issues requiring attention\n3. Action items\n4. Open discussion topics\n\nFormat it professionally.",
               "max_words": 300}, 600, 200),
        _node("n4", "send_email", "Send Meeting Invite",
              {"to": "", "subject": "Weekly Business Review — {date} | Agenda Attached",
               "body_mode": "use_previous_output", "require_approval": True}, 900, 200),
        _node("n5", "save_file", "Archive Agenda",
              {"filename_template": "meeting_agenda_{date}", "format": "txt"}, 900, 350),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4"),
        _edge("n3", "n5"),
    ],
}

# ── Template 8: Call Scheduler & Prep ────────────────────────────────────────
CALL_SCHEDULER: Dict[str, Any] = {
    "name": "Call Scheduler & Prep",
    "description": "Prepare for a client call: pull their data, search docs for context, draft talking points, and send a prep email.",
    "enabled": False,
    "tags": ["call", "scheduling", "client", "ai-prep"],
    "nodes": [
        _node("n1", "manual_trigger", "Prep for Call",
              {"label": "Prepare Call Brief"}, 100, 200),
        _node("n2", "sql_query", "Client's Order History",
              {"mode": "natural_language",
               "question": "Show the most recent 10 orders with amounts and status",
               "max_rows": 10}, 350, 100),
        _node("n3", "rag_search", "Search Relevant Docs",
              {"query": "client communication guidelines and escalation procedures",
               "top_k": 3}, 350, 300),
        _node("n4", "llm_prompt", "Draft Talking Points",
              {"prompt": "Prepare a call brief with talking points based on:\n\nCLIENT DATA:\n{input}\n\nInclude:\n1. Account summary\n2. Key talking points\n3. Potential concerns to address\n4. Recommended next steps\n5. Suggested call duration: 15-30 min",
               "max_words": 350}, 650, 200),
        _node("n5", "send_email", "Send Prep to Self",
              {"to": "", "subject": "Call Prep Brief — {date}",
               "body_mode": "use_previous_output", "require_approval": True}, 950, 200),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n1", "n3"),
        _edge("n2", "n4"),
        _edge("n3", "n4"),
        _edge("n4", "n5"),
    ],
}

# ── Template 9: Live Data Fetcher & Analyzer ─────────────────────────────────
LIVE_DATA_ANALYZER: Dict[str, Any] = {
    "name": "Live Data Fetcher & Analyzer",
    "description": "Fetch data from a web source, analyze it with AI, classify importance, store insights in the database.",
    "enabled": False,
    "tags": ["web", "live-data", "analysis", "storage"],
    "nodes": [
        _node("n1", "schedule_trigger", "Every 6 Hours",
              {"mode": "interval", "interval_minutes": 360}, 100, 200),
        _node("n2", "web_search", "Fetch Latest Data",
              {"query": "latest business trends market analysis 2025",
               "max_results": 5}, 350, 200),
        _node("n3", "llm_prompt", "Analyze & Extract Insights",
              {"prompt": "Analyze these search results and extract key business insights:\n\n{input}\n\nFor each insight, provide:\n- Topic\n- Summary (1-2 sentences)\n- Relevance score (high/medium/low)\n- Recommended action",
               "max_words": 400}, 600, 200),
        _node("n4", "classify", "Classify Urgency",
              {"categories": "urgent,important,informational",
               "field": "input"}, 850, 200),
        _node("n5", "save_file", "Store in DB",
              {"filename_template": "market_intel_{date}_{time}", "format": "txt"}, 1100, 100),
        _node("n6", "discord_notify", "Alert if Urgent",
              {"title": "Urgent Market Intel",
               "message": "{input}", "severity": "high"}, 1100, 300),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4"),
        _edge("n4", "n5", "informational"),
        _edge("n4", "n5", "important"),
        _edge("n4", "n6", "urgent"),
    ],
}

# ── Template 10: Customer Churn Early Warning ────────────────────────────────
CUSTOMER_CHURN_WARNING: Dict[str, Any] = {
    "name": "Customer Churn Early Warning",
    "description": "Daily: identify customers with declining orders, analyze risk, alert sales team with action plan.",
    "enabled": False,
    "tags": ["customers", "churn", "ai-analysis", "alerts"],
    "nodes": [
        _node("n1", "schedule_trigger", "Daily 10:00",
              {"mode": "daily", "daily_time": "10:00"}, 100, 200),
        _node("n2", "sql_query", "Find At-Risk Customers",
              {"mode": "natural_language",
               "question": "Show customers whose order count this month is less than half their average monthly orders, with their total spend",
               "max_rows": 20}, 350, 200),
        _node("n3", "data_exists_condition", "Any At-Risk?",
              {"min_rows": 1}, 600, 200),
        _node("n4", "llm_prompt", "Analyze Churn Risk",
              {"prompt": "These customers show declining engagement:\n\n{input}\n\nFor each, provide:\n1. Risk level (high/medium)\n2. Likely reason\n3. Recommended retention action\n4. Priority (1-5)\n\nFormat as a clear action plan for the sales team.",
               "max_words": 400}, 850, 100),
        _node("n5", "send_email", "Alert Sales Team",
              {"to": "", "subject": "Customer Churn Alert — {date} — Action Required",
               "body_mode": "use_previous_output", "require_approval": True}, 1100, 100),
        _node("n6", "save_file", "Log Check",
              {"filename_template": "churn_check_{date}", "format": "txt"}, 850, 350),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4", "has_data"),
        _edge("n3", "n6", "empty"),
        _edge("n4", "n5"),
    ],
}

# ── Template 11: Slack Daily Standup Digest ──────────────────────────────────
SLACK_DAILY_DIGEST: Dict[str, Any] = {
    "name": "Slack Daily Digest",
    "description": "Every weekday 09:00: post a summary of yesterday's key numbers to Slack.",
    "enabled": False,
    "tags": ["slack", "digest", "scheduled"],
    "nodes": [
        _node("n1", "schedule_trigger", "Weekdays 09:00",
              {"mode": "daily", "daily_time": "09:00"}, 100, 100),
        _node("n2", "sql_query", "Yesterday's Numbers",
              {"mode": "natural_language",
               "question": "Show yesterday's total sales, top 3 products, and top 3 regions",
               "max_rows": 20}, 350, 100),
        _node("n3", "summarize", "Build Digest",
              {"style": "bullet_points", "max_points": 6}, 600, 100),
        _node("n4", "slack_notify", "Post to Slack",
              {"title": "Daily Digest", "message": "{input}", "severity": "info"}, 850, 100),
    ],
    "edges": [
        _edge("n1", "n2"),
        _edge("n2", "n3"),
        _edge("n3", "n4"),
    ],
}


TEMPLATES: List[Dict[str, Any]] = [
    DAILY_SALES_REPORT,
    ANOMALY_ALERT_PIPELINE,
    WEEKLY_KPI_DIGEST,
    DOCUMENT_MONITOR,
    REVENUE_DROP_RESPONSE,
    AUTO_EMAIL_SENDER,
    SLACK_DAILY_DIGEST,
    MEETING_SCHEDULER,
    CALL_SCHEDULER,
    LIVE_DATA_ANALYZER,
    CUSTOMER_CHURN_WARNING,
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
