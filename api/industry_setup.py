"""Industry workspace presets.

Onboarding uses these presets after a new user selects an industry. The goal is
not to remove product surface area. Every business keeps access to every module;
the preset simply tunes the first-run workspace so the most relevant agents,
templates, and next actions are ready immediately.
"""
from __future__ import annotations

import json
from typing import Dict, List

from config.db import get_conn
from utils.timez import now_iso

PRESETS: Dict[str, Dict] = {
    "Healthcare": {
        "tools": ["Patient intake", "Policy knowledge base", "Appointment follow-ups", "Privacy review"],
        "priority_agents": ["email_triage", "meeting_prep", "morning_briefing", "memory_consolidate"],
        "schedules": {"email_triage": 15, "meeting_prep": 10, "memory_consolidate": 10080},
        "templates": [
            {
                "name": "Appointment follow-up",
                "subject": "Next steps after your appointment with {{company_name}}",
                "body": "Hi {{first_name}},\n\nThank you for speaking with us. Your next step is {{next_step}}. If you have questions, reply here and our team will help.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Policy document request",
                "subject": "Documents needed for {{case_reference}}",
                "body": "Hi {{first_name}},\n\nTo move forward with {{case_reference}}, please share {{documents_needed}}. We will use these only for the current request.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Real estate": {
        "tools": ["Lead capture", "Property documents", "Buyer follow-ups", "Deal pipeline"],
        "priority_agents": ["stale_deal_watcher", "meeting_prep", "outbound_caller", "email_triage"],
        "schedules": {"stale_deal_watcher": 1440, "meeting_prep": 10, "email_triage": 15},
        "templates": [
            {
                "name": "Property follow-up",
                "subject": "Details for {{property_name}}",
                "body": "Hi {{first_name}},\n\nSharing the next details for {{property_name}}. Budget: {{budget}}. Preferred visit time: {{visit_time}}.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Site visit confirmation",
                "subject": "Confirmed: {{property_name}} visit on {{visit_date}}",
                "body": "Hi {{first_name}},\n\nYour site visit for {{property_name}} is confirmed for {{visit_date}} at {{visit_time}}. Reply here if anything changes.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Education": {
        "tools": ["Admissions support", "Course FAQ", "Student follow-ups", "Reports"],
        "priority_agents": ["email_triage", "morning_briefing", "meeting_prep", "memory_consolidate"],
        "schedules": {"email_triage": 30, "morning_briefing": 1440, "meeting_prep": 10},
        "templates": [
            {
                "name": "Admissions follow-up",
                "subject": "Next steps for {{program_name}} admission",
                "body": "Hi {{first_name}},\n\nThanks for your interest in {{program_name}}. Please complete {{next_step}} by {{deadline}}.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Course FAQ reply",
                "subject": "About {{course_name}}",
                "body": "Hi {{first_name}},\n\nHere are the details for {{course_name}}: {{course_detail}}. I can also help with fees, schedule, and admission steps.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Legal": {
        "tools": ["Client intake", "Document Q&A", "Case task tracking", "Secure audit trail"],
        "priority_agents": ["meeting_prep", "email_triage", "memory_consolidate", "morning_briefing"],
        "schedules": {"meeting_prep": 10, "email_triage": 30, "memory_consolidate": 10080},
        "templates": [
            {
                "name": "Client intake request",
                "subject": "Information needed for {{matter_name}}",
                "body": "Hi {{first_name}},\n\nTo prepare for {{matter_name}}, please share {{documents_needed}} and any key dates we should know.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Case update",
                "subject": "Update on {{matter_name}}",
                "body": "Hi {{first_name}},\n\nQuick update on {{matter_name}}: {{case_update}}. Next action: {{next_action}}.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Ecommerce": {
        "tools": ["Product catalog", "Returns support", "Order follow-ups", "Customer inbox"],
        "priority_agents": ["email_triage", "invoice_reminder", "stale_deal_watcher", "morning_briefing"],
        "schedules": {"email_triage": 15, "invoice_reminder": 1440, "stale_deal_watcher": 1440},
        "templates": [
            {
                "name": "Order follow-up",
                "subject": "Update on order {{order_id}}",
                "body": "Hi {{first_name}},\n\nYour order {{order_id}} is currently {{order_status}}. Expected next step: {{next_step}}.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Return request reply",
                "subject": "Return request for {{order_id}}",
                "body": "Hi {{first_name}},\n\nWe received your return request for {{order_id}}. Please share {{required_info}} so we can process it quickly.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Finance": {
        "tools": ["Client onboarding", "Invoice reminders", "Compliance docs", "Secure reporting"],
        "priority_agents": ["invoice_reminder", "email_triage", "meeting_prep", "memory_consolidate"],
        "schedules": {"invoice_reminder": 1440, "email_triage": 30, "meeting_prep": 10},
        "templates": [
            {
                "name": "Payment reminder",
                "subject": "Reminder: invoice {{invoice_number}}",
                "body": "Hi {{first_name}},\n\nThis is a reminder that invoice {{invoice_number}} for {{amount}} is due on {{due_date}}. Please let us know if you need anything from our side.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Document checklist",
                "subject": "Documents needed for {{service_name}}",
                "body": "Hi {{first_name}},\n\nFor {{service_name}}, please share {{documents_needed}}. We will review and confirm the next step.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "SaaS": {
        "tools": ["Pipeline CRM", "Support triage", "Churn signals", "Product knowledge base"],
        "priority_agents": ["stale_deal_watcher", "email_triage", "meeting_prep", "morning_briefing"],
        "schedules": {"stale_deal_watcher": 1440, "email_triage": 15, "meeting_prep": 10},
        "templates": [
            {
                "name": "Demo follow-up",
                "subject": "Next steps after the {{product_name}} demo",
                "body": "Hi {{first_name}},\n\nThanks for joining the demo. Based on {{pain_point}}, the best next step is {{next_step}}.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Renewal check-in",
                "subject": "Checking in before {{renewal_date}}",
                "body": "Hi {{first_name}},\n\nYour renewal is coming up on {{renewal_date}}. Are there any blockers, usage questions, or team changes we should help with?\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Manufacturing": {
        "tools": ["Vendor docs", "Order follow-ups", "Operations tasks", "Reports"],
        "priority_agents": ["morning_briefing", "email_triage", "invoice_reminder", "meeting_prep"],
        "schedules": {"morning_briefing": 1440, "email_triage": 30, "invoice_reminder": 1440},
        "templates": [
            {
                "name": "Vendor follow-up",
                "subject": "Status request for {{purchase_order}}",
                "body": "Hi {{first_name}},\n\nPlease share the latest status for {{purchase_order}}, including dispatch date, blockers, and expected delivery.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Delivery update",
                "subject": "Delivery update for {{order_id}}",
                "body": "Hi {{first_name}},\n\nUpdate for {{order_id}}: {{delivery_status}}. Next checkpoint: {{next_checkpoint}}.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Hospitality": {
        "tools": ["Booking support", "Guest FAQs", "Review follow-ups", "Shift tasks"],
        "priority_agents": ["email_triage", "morning_briefing", "evening_digest", "meeting_prep"],
        "schedules": {"email_triage": 15, "morning_briefing": 1440, "evening_digest": 1440},
        "templates": [
            {
                "name": "Booking confirmation",
                "subject": "Booking confirmed for {{booking_date}}",
                "body": "Hi {{first_name}},\n\nYour booking is confirmed for {{booking_date}} at {{booking_time}}. Notes: {{booking_notes}}.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Guest review request",
                "subject": "How was your visit to {{business_name}}?",
                "body": "Hi {{first_name}},\n\nThank you for visiting us. If you have a minute, we would love your feedback: {{review_link}}.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Local services": {
        "tools": ["Lead intake", "Job scheduling", "Quote follow-ups", "Invoice reminders"],
        "priority_agents": ["outbound_caller", "invoice_reminder", "email_triage", "stale_deal_watcher"],
        "schedules": {"email_triage": 15, "invoice_reminder": 1440, "stale_deal_watcher": 1440},
        "templates": [
            {
                "name": "Quote follow-up",
                "subject": "Following up on quote {{quote_number}}",
                "body": "Hi {{first_name}},\n\nChecking whether you had questions on quote {{quote_number}} for {{service_name}}. We can start on {{start_date}} if that works.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Job scheduling",
                "subject": "Scheduling {{service_name}}",
                "body": "Hi {{first_name}},\n\nWe can schedule {{service_name}} on {{slot_options}}. Reply with the option that works best.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
    "Consulting": {
        "tools": ["Client briefs", "Proposal docs", "Meeting prep", "Project tasks"],
        "priority_agents": ["meeting_prep", "morning_briefing", "stale_deal_watcher", "email_triage"],
        "schedules": {"meeting_prep": 10, "morning_briefing": 1440, "email_triage": 30},
        "templates": [
            {
                "name": "Proposal follow-up",
                "subject": "Following up on {{proposal_name}}",
                "body": "Hi {{first_name}},\n\nFollowing up on {{proposal_name}}. Happy to clarify scope, timeline, or pricing before the next step.\n\nRegards,\n{{sender_name}}",
            },
            {
                "name": "Meeting recap",
                "subject": "Recap and next steps from {{meeting_name}}",
                "body": "Hi {{first_name}},\n\nRecap from {{meeting_name}}: {{summary}}. Next actions: {{next_actions}}.\n\nRegards,\n{{sender_name}}",
            },
        ],
    },
}

DEFAULT_PRESET = {
    "tools": ["Business knowledge base", "CRM pipeline", "Task automation", "Reports"],
    "priority_agents": ["morning_briefing", "email_triage", "meeting_prep", "memory_consolidate"],
    "schedules": {"morning_briefing": 1440, "email_triage": 30, "meeting_prep": 10},
    "templates": [
        {
            "name": "General follow-up",
            "subject": "Following up on {{topic}}",
            "body": "Hi {{first_name}},\n\nFollowing up on {{topic}}. Next step: {{next_step}}.\n\nRegards,\n{{sender_name}}",
        },
        {
            "name": "Document request",
            "subject": "Documents needed for {{project_name}}",
            "body": "Hi {{first_name}},\n\nPlease share {{documents_needed}} for {{project_name}} when you can.\n\nRegards,\n{{sender_name}}",
        },
    ],
}


def normalize_industry(industry: str) -> str:
    raw = (industry or "").strip()
    for key in PRESETS:
        if key.lower() == raw.lower():
            return key
    return "Other"


def get_preset(industry: str) -> Dict:
    key = normalize_industry(industry)
    preset = PRESETS.get(key, DEFAULT_PRESET)
    return {
        "industry": key,
        "tools": list(preset["tools"]),
        "priority_agents": list(preset["priority_agents"]),
        "schedules": dict(preset["schedules"]),
        "templates": [dict(t) for t in preset["templates"]],
    }


def _read_business(business_id: str) -> Dict:
    from api.businesses import BUSINESSES_TABLE

    conn = get_conn()
    conn.row_factory = None
    try:
        row = conn.execute(
            f"SELECT industry, settings FROM {BUSINESSES_TABLE} WHERE id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"industry": "", "settings": {}}
    settings = {}
    try:
        settings = json.loads(row[1] or "{}")
    except Exception:
        settings = {}
    return {"industry": row[0] or "", "settings": settings}


def _write_settings(business_id: str, settings: Dict) -> None:
    from api.businesses import BUSINESSES_TABLE

    conn = get_conn()
    try:
        conn.execute(
            f"UPDATE {BUSINESSES_TABLE} SET settings = ?, updated_at = ? WHERE id = ?",
            (json.dumps(settings), now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_templates(business_id: str, user_id: str, templates: List[Dict]) -> List[str]:
    from api import email_templates

    existing = {t["name"].strip().lower() for t in email_templates.list_templates(business_id)}
    created: List[str] = []
    for tpl in templates:
        if tpl["name"].strip().lower() in existing:
            continue
        created_tpl = email_templates.create_template(business_id, user_id, tpl)
        created.append(created_tpl["name"])
        existing.add(tpl["name"].strip().lower())
    return created


def apply_industry_setup(
    business_id: str,
    user_id: str,
    industry: str | None = None,
    *,
    seed_sample_data: bool = True,
) -> Dict:
    """Apply agent schedules, feature focus, starter templates, AND drop
    industry-flavoured seed data into the workspace if it's empty.

    Idempotent on every layer:
      - personas/schedules: re-applying tunes the same rows
      - templates: only missing names are created
      - seed data: skipped entirely if the business already has CRM rows

    Args:
        seed_sample_data: set False when the caller already has real data
            and just wants to re-tune the preset (e.g. an industry change
            on an existing workspace).
    """
    business = _read_business(business_id)
    preset = get_preset(industry or business["industry"])

    from agents import personas
    from api import agent_schedule

    # Keep all built-ins available. Priority agents simply get explicit enabled
    # rows and tuned schedules so the workspace feels ready on first login.
    enabled: List[str] = []
    for agent_key in personas.DEFAULTS.keys():
        personas.set_enabled(business_id, agent_key, True)
        enabled.append(agent_key)

    schedules: Dict[str, int] = {}
    for agent_key, minutes in preset["schedules"].items():
        agent_schedule.set_interval(business_id, agent_key, minutes)
        schedules[agent_key] = minutes

    created_templates = _ensure_templates(business_id, user_id, preset["templates"])

    # Drop industry-flavoured CRM data so the dashboard isn't empty on Day 1.
    # The seeder has its own existence check — won't pollute real data.
    # Failure here MUST NOT block onboarding (e.g. if the industry isn't in
    # INDUSTRY_DATA we just skip silently and the user gets a clean workspace).
    seed_result: Dict[str, object] = {"seeded": False, "reason": "skipped"}
    if seed_sample_data:
        try:
            from api.industry_seed import seed_industry_sample
            seed_result = seed_industry_sample(business_id, user_id, preset["industry"])
        except Exception as e:
            from loguru import logger
            logger.warning(f"[IndustrySetup] seed step failed (non-fatal): {e}")
            seed_result = {"seeded": False, "reason": f"error: {e!s}"[:200]}

    settings = business["settings"]
    settings["industry_setup"] = {
        "industry": preset["industry"],
        "recommended_tools": preset["tools"],
        "priority_agents": preset["priority_agents"],
        "schedules": schedules,
        "seed": seed_result,
        "applied_at": now_iso(),
    }
    _write_settings(business_id, settings)

    return {
        "industry": preset["industry"],
        "recommended_tools": preset["tools"],
        "priority_agents": preset["priority_agents"],
        "enabled_agents": enabled,
        "schedules": schedules,
        "created_templates": created_templates,
        "seed": seed_result,
    }
