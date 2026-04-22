"""
Node Registry — defines every available node type, its category, config schema,
display properties, and UI form fields.

Each node type entry:
  category    : trigger | condition | data | ai | action | control
  name        : human-readable label
  icon        : emoji shown in canvas
  color       : hex color for the node bubble
  description : tooltip / help text
  config      : dict of config fields → each field has type, label, default, required
  outputs     : list of named output ports (for condition branching)
"""

NODE_TYPES: dict = {

    # ── TRIGGERS ─────────────────────────────────────────────────────────────
    "schedule_trigger": {
        "category": "trigger",
        "name": "Schedule",
        "icon": "⏰",
        "color": "#1565c0",
        "description": "Run workflow on a cron schedule or fixed interval",
        "config": {
            "mode": {
                "type": "select", "label": "Trigger mode",
                "options": ["interval", "cron", "daily", "weekly"],
                "default": "daily",
            },
            "interval_minutes": {
                "type": "number", "label": "Interval (minutes)",
                "default": 60, "min": 1, "max": 10080,
                "show_if": {"mode": "interval"},
            },
            "cron_expression": {
                "type": "text", "label": "Cron expression (e.g. 0 8 * * *)",
                "default": "0 8 * * *",
                "show_if": {"mode": "cron"},
            },
            "daily_time": {
                "type": "text", "label": "Time (HH:MM 24h)",
                "default": "08:00",
                "show_if": {"mode": "daily"},
            },
            "weekly_day": {
                "type": "select", "label": "Day of week",
                "options": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
                "default": "Monday",
                "show_if": {"mode": "weekly"},
            },
            "weekly_time": {
                "type": "text", "label": "Time (HH:MM 24h)",
                "default": "09:00",
                "show_if": {"mode": "weekly"},
            },
        },
        "outputs": ["triggered"],
    },

    "manual_trigger": {
        "category": "trigger",
        "name": "Manual",
        "icon": "▶️",
        "color": "#1565c0",
        "description": "Run workflow by clicking a button in the UI",
        "config": {
            "label": {
                "type": "text", "label": "Button label",
                "default": "Run Workflow",
            },
        },
        "outputs": ["triggered"],
    },

    "anomaly_trigger": {
        "category": "trigger",
        "name": "Anomaly Detected",
        "icon": "🚨",
        "color": "#b71c1c",
        "description": "Fires when the proactive monitor detects a data anomaly",
        "config": {
            "threshold_pct": {
                "type": "number", "label": "Drop threshold (%)",
                "default": 15, "min": 1, "max": 99,
            },
            "regions": {
                "type": "multiselect", "label": "Watch regions (empty = all)",
                "options": ["North","South","East","West","Central"],
                "default": [],
            },
        },
        "outputs": ["anomaly_found"],
    },

    "webhook_trigger": {
        "category": "trigger",
        "name": "Webhook",
        "icon": "🌐",
        "color": "#1565c0",
        "description": "Trigger via HTTP POST to a local endpoint",
        "config": {
            "path": {
                "type": "text", "label": "Endpoint path",
                "default": "/webhook/my-workflow",
            },
            "secret": {
                "type": "password", "label": "Shared secret (optional)",
                "default": "",
            },
        },
        "outputs": ["received"],
    },

    # ── CONDITIONS ────────────────────────────────────────────────────────────
    "value_condition": {
        "category": "condition",
        "name": "Value Check",
        "icon": "⚖️",
        "color": "#e65100",
        "description": "Branch based on a numeric or text value from the previous node",
        "config": {
            "field": {
                "type": "text", "label": "Field name (from previous output)",
                "default": "revenue",
            },
            "operator": {
                "type": "select", "label": "Operator",
                "options": ["<", "<=", ">", ">=", "==", "!=", "contains", "not_contains"],
                "default": "<",
            },
            "threshold": {
                "type": "text", "label": "Threshold value",
                "default": "10000",
            },
        },
        "outputs": ["true", "false"],
    },

    "llm_condition": {
        "category": "condition",
        "name": "AI Decision",
        "icon": "🧠",
        "color": "#6a1b9a",
        "description": "Ask the local LLM to make a yes/no decision based on data",
        "config": {
            "question": {
                "type": "textarea",
                "label": "Decision question (use {data} for previous output)",
                "default": "Based on this data: {data}\nIs this situation critical and requires immediate action? Answer YES or NO.",
            },
        },
        "outputs": ["yes", "no"],
    },

    "data_exists_condition": {
        "category": "condition",
        "name": "Data Exists",
        "icon": "🔍",
        "color": "#e65100",
        "description": "Check if the previous node returned any data",
        "config": {
            "min_rows": {
                "type": "number", "label": "Minimum rows required",
                "default": 1, "min": 1,
            },
        },
        "outputs": ["has_data", "empty"],
    },

    # ── DATA NODES ────────────────────────────────────────────────────────────
    "sql_query": {
        "category": "data",
        "name": "SQL Query",
        "icon": "🗄️",
        "color": "#2e7d32",
        "description": "Run a SQL query against the database. Use natural language or raw SQL.",
        "config": {
            "mode": {
                "type": "select", "label": "Input mode",
                "options": ["natural_language", "raw_sql"],
                "default": "natural_language",
            },
            "question": {
                "type": "textarea",
                "label": "Natural language question",
                "default": "Show total revenue by region for the last 30 days",
                "show_if": {"mode": "natural_language"},
            },
            "sql": {
                "type": "textarea",
                "label": "Raw SQL query",
                "default": "SELECT region, SUM(revenue) as total FROM sales_metrics GROUP BY region",
                "show_if": {"mode": "raw_sql"},
            },
            "max_rows": {
                "type": "number", "label": "Max rows", "default": 100,
            },
        },
        "outputs": ["data"],
    },

    "rag_search": {
        "category": "data",
        "name": "Document Search",
        "icon": "📄",
        "color": "#1565c0",
        "description": "Search the knowledge base (uploaded documents) for relevant information",
        "config": {
            "query": {
                "type": "textarea", "label": "Search query (use {input} for dynamic input)",
                "default": "What is our refund policy?",
            },
            "top_k": {
                "type": "number", "label": "Results to retrieve", "default": 3,
            },
        },
        "outputs": ["results"],
    },

    "web_search": {
        "category": "data",
        "name": "Web Search",
        "icon": "🌐",
        "color": "#00695c",
        "description": "Search the web using DuckDuckGo (no API key needed)",
        "config": {
            "query": {
                "type": "textarea",
                "label": "Search query (use {input} for dynamic content)",
                "default": "latest business news India",
            },
            "max_results": {
                "type": "number", "label": "Max results", "default": 5,
            },
        },
        "outputs": ["results"],
    },

    "data_transform": {
        "category": "data",
        "name": "Transform",
        "icon": "🔄",
        "color": "#37474f",
        "description": "Filter, sort, or aggregate data from the previous node",
        "config": {
            "operation": {
                "type": "select", "label": "Operation",
                "options": ["top_n", "filter_column", "sort", "sum_column", "format_text"],
                "default": "top_n",
            },
            "n": {
                "type": "number", "label": "N (for top_n)", "default": 5,
                "show_if": {"operation": "top_n"},
            },
            "column": {
                "type": "text", "label": "Column name",
                "default": "revenue",
            },
            "text_template": {
                "type": "textarea",
                "label": "Text template (use {row.col_name})",
                "default": "Region: {row.region}, Revenue: {row.revenue}",
                "show_if": {"operation": "format_text"},
            },
        },
        "outputs": ["transformed"],
    },

    # ── AI NODES ──────────────────────────────────────────────────────────────
    "llm_prompt": {
        "category": "ai",
        "name": "AI Prompt",
        "icon": "💬",
        "color": "#6a1b9a",
        "description": "Send a custom prompt to the local LLM. Use {input} for previous output.",
        "config": {
            "prompt": {
                "type": "textarea",
                "label": "Prompt template",
                "default": "Summarize this business data in 3 bullet points:\n\n{input}",
            },
            "model": {
                "type": "select", "label": "Model override (empty = default)",
                "options": ["default", "llama3.1:8b-instruct-q4_K_M",
                            "qwen2.5:3b-instruct-q4_K_M", "llama3.2:3b"],
                "default": "default",
            },
            "max_words": {
                "type": "number", "label": "Max response words (0 = unlimited)",
                "default": 0,
            },
        },
        "outputs": ["response"],
    },

    "summarize": {
        "category": "ai",
        "name": "Summarize",
        "icon": "📝",
        "color": "#6a1b9a",
        "description": "Summarize the input data or text into key points",
        "config": {
            "style": {
                "type": "select", "label": "Summary style",
                "options": ["bullet_points", "paragraph", "executive", "one_line"],
                "default": "bullet_points",
            },
            "max_points": {
                "type": "number", "label": "Max bullet points", "default": 5,
            },
        },
        "outputs": ["summary"],
    },

    "generate_report": {
        "category": "ai",
        "name": "Generate PDF",
        "icon": "📊",
        "color": "#4a148c",
        "description": "Generate a professional PDF report from data",
        "config": {
            "title": {
                "type": "text", "label": "Report title",
                "default": "Auto-Generated Report",
            },
            "include_chart": {
                "type": "boolean", "label": "Include chart", "default": True,
            },
            "chart_type": {
                "type": "select", "label": "Chart type",
                "options": ["auto", "bar", "line", "pie"],
                "default": "auto",
            },
        },
        "outputs": ["pdf_path"],
    },

    "classify": {
        "category": "ai",
        "name": "AI Classify",
        "icon": "🏷️",
        "color": "#6a1b9a",
        "description": "Classify or tag input data using the local LLM",
        "config": {
            "categories": {
                "type": "text",
                "label": "Categories (comma-separated)",
                "default": "positive, negative, neutral",
            },
            "field": {
                "type": "text", "label": "Field to classify (from input)",
                "default": "text",
            },
        },
        "outputs": ["classification"],
    },

    # ── ACTION NODES ──────────────────────────────────────────────────────────
    "send_email": {
        "category": "action",
        "name": "Send Email",
        "icon": "📧",
        "color": "#bf360c",
        "description": "Draft and send an email. Requires Gmail credentials in .env.",
        "config": {
            "to": {
                "type": "text", "label": "Recipient email(s) (comma-separated)",
                "default": "",
            },
            "subject": {
                "type": "text", "label": "Subject (use {input} for dynamic content)",
                "default": "NexusAgent Report",
            },
            "body_mode": {
                "type": "select", "label": "Body",
                "options": ["use_previous_output", "custom", "ai_draft"],
                "default": "use_previous_output",
            },
            "custom_body": {
                "type": "textarea", "label": "Custom body (use {input})",
                "default": "{input}",
                "show_if": {"body_mode": "custom"},
            },
            "require_approval": {
                "type": "boolean", "label": "Require human approval before sending",
                "default": True,
            },
        },
        "outputs": ["sent", "pending_approval"],
    },

    "discord_notify": {
        "category": "action",
        "name": "Discord / Notify",
        "icon": "🔔",
        "color": "#4527a0",
        "description": "Send a notification via Discord webhook or desktop alert",
        "config": {
            "title": {
                "type": "text", "label": "Alert title",
                "default": "NexusAgent Alert",
            },
            "message": {
                "type": "textarea",
                "label": "Message (use {input} for dynamic content)",
                "default": "{input}",
            },
            "severity": {
                "type": "select", "label": "Severity",
                "options": ["info", "warning", "critical", "success"],
                "default": "info",
            },
        },
        "outputs": ["notified"],
    },

    "http_request": {
        "category": "action",
        "name": "HTTP Request",
        "icon": "🔗",
        "color": "#00695c",
        "description": "Call an external API (Slack, Teams, custom webhook, etc.)",
        "config": {
            "url": {
                "type": "text", "label": "URL",
                "default": "https://hooks.slack.com/services/YOUR/WEBHOOK",
            },
            "method": {
                "type": "select", "label": "Method",
                "options": ["POST", "GET", "PUT", "PATCH"],
                "default": "POST",
            },
            "headers_json": {
                "type": "textarea",
                "label": 'Headers (JSON, e.g. {"Authorization": "Bearer TOKEN"})',
                "default": '{"Content-Type": "application/json"}',
            },
            "body_template": {
                "type": "textarea",
                "label": 'Body template (JSON, use {input})',
                "default": '{"text": "{input}"}',
            },
            "api_key_name": {
                "type": "text",
                "label": "API key name (from API Keys config)",
                "default": "",
            },
        },
        "outputs": ["response"],
    },

    "save_file": {
        "category": "action",
        "name": "Save File",
        "icon": "💾",
        "color": "#37474f",
        "description": "Save output to a file in the outputs/ folder",
        "config": {
            "filename_template": {
                "type": "text",
                "label": "Filename (use {date}, {time}, {workflow_name})",
                "default": "{workflow_name}_{date}.txt",
            },
            "format": {
                "type": "select", "label": "Format",
                "options": ["txt", "csv", "json"],
                "default": "txt",
            },
        },
        "outputs": ["saved"],
    },

    "desktop_notify": {
        "category": "action",
        "name": "Desktop Alert",
        "icon": "💻",
        "color": "#4527a0",
        "description": "Show a desktop notification popup",
        "config": {
            "title": {
                "type": "text", "label": "Notification title",
                "default": "NexusAgent",
            },
            "message": {
                "type": "textarea", "label": "Message (use {input})",
                "default": "{input}",
            },
        },
        "outputs": ["done"],
    },

    # ── CONTROL NODES ─────────────────────────────────────────────────────────
    "wait_node": {
        "category": "control",
        "name": "Wait / Delay",
        "icon": "⏳",
        "color": "#546e7a",
        "description": "Pause workflow execution for a specified duration",
        "config": {
            "seconds": {
                "type": "number", "label": "Wait duration (seconds)",
                "default": 5, "min": 1,
            },
        },
        "outputs": ["done"],
    },

    "merge_node": {
        "category": "control",
        "name": "Merge",
        "icon": "🔀",
        "color": "#546e7a",
        "description": "Merge outputs from multiple branches into one",
        "config": {
            "strategy": {
                "type": "select", "label": "Merge strategy",
                "options": ["concat_text", "concat_list", "first_available"],
                "default": "concat_text",
            },
        },
        "outputs": ["merged"],
    },
}

# ── Lookup helpers ────────────────────────────────────────────────────────────
CATEGORY_ORDER = ["trigger", "condition", "data", "ai", "action", "control"]

CATEGORY_LABELS = {
    "trigger": "Triggers",
    "condition": "Conditions",
    "data": "Data",
    "ai": "AI",
    "action": "Actions",
    "control": "Control",
}

def get_node_def(node_type: str) -> dict:
    return NODE_TYPES.get(node_type, {})

def get_nodes_by_category() -> dict:
    result = {cat: [] for cat in CATEGORY_ORDER}
    for k, v in NODE_TYPES.items():
        cat = v.get("category", "control")
        if cat in result:
            result[cat].append((k, v))
    return result
