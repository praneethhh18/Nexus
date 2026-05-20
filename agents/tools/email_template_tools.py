"""Agent-facing tools for the email templates feature.

Surfaces reusable templates (subject + body with {{var}} placeholders) to the
agent so the LLM can:
    - List existing templates
    - Create a new template from a draft it just wrote
    - Send an email by picking a template + filling variables (uses the same
      Gmail SMTP path as the existing send_email tool, no separate sender)

Sample WhatsApp interactions this enables:
    "Send my invoice reminder template to all overdue contacts."
    "Save this email as a template called 'monsoon discount'."
    "What email templates do I have?"
"""
from __future__ import annotations

from typing import Any, Dict

from loguru import logger

from agents.tool_registry import register_tool


# ── List ────────────────────────────────────────────────────────────────────
def _list_templates(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import email_templates as _et
    rows = _et.list_templates(ctx["business_id"])
    return {
        "ok":        True,
        "count":     len(rows),
        "templates": [
            {
                "id":        t["id"],
                "name":      t["name"],
                "subject":   t["subject"],
                "variables": t.get("variables", []),
                "preview":   (t["body"] or "")[:200],
            }
            for t in rows
        ],
    }


register_tool(
    name="list_email_templates",
    description="List all reusable email templates for this business with their variables and a 200-char body preview.",
    input_schema={"type": "object", "properties": {}},
    handler=_list_templates,
    summary_fn=lambda a: "List email templates",
)


# Placeholder strings the LLM was generating instead of real content
# (e.g. it wrote body='(body)' or subject='(subject)' as a stub). We
# refuse these at the tool layer so the model has to write the actual
# email content before we save anything. Catches the failure that
# saved 'Business Enquiry Visit Tomorrow' / body='(body)' as a template.
_PLACEHOLDER_BODIES = {
    "", "(body)", "(subject)", "(content)", "(message)",
    "body", "subject", "content", "tbd", "todo", "to be filled",
    "<body>", "<subject>", "{body}", "{subject}",
    "...", "…",
}


def _is_placeholder(s: str) -> bool:
    return (s or "").strip().lower() in _PLACEHOLDER_BODIES


# ── Create ──────────────────────────────────────────────────────────────────
def _create_template(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import email_templates as _et
    name    = args.get("name") or ""
    subject = args.get("subject") or ""
    body    = args.get("body") or ""

    # Validate against placeholder garbage. If the LLM tries to save a
    # template with body='(body)' the user ends up with a dead template
    # they can't use. Bounce it back with a clear error so the agent
    # retries with real content.
    if _is_placeholder(subject) or len(subject.strip()) < 5:
        raise ValueError(
            "Subject is too short or a placeholder. Write the actual "
            "email subject (e.g. 'Quick check-in on the Q3 invoice'), "
            "not a stub like '(subject)'."
        )
    if _is_placeholder(body) or len(body.strip()) < 20:
        raise ValueError(
            "Body is empty or a placeholder. Write the actual email "
            "content (greeting + 1-3 sentences + sign-off). Saving "
            "templates with stubs like '(body)' makes the library "
            "useless. Try again with the real text."
        )

    tpl = _et.create_template(ctx["business_id"], ctx["user_id"], {
        "name":    name,
        "subject": subject,
        "body":    body,
    })
    return {
        "ok":        True,
        "id":        tpl["id"],
        "name":      tpl["name"],
        "variables": tpl.get("variables", []),
        "message":   f"Saved template '{tpl['name']}' with {len(tpl.get('variables', []))} variable(s).",
    }


register_tool(
    name="create_email_template",
    description=(
        "Save a reusable email template to the workspace library. This "
        "does NOT send an email to anyone — it only stores the template "
        "for later use. To actually send an email, call `send_email` (or "
        "`send_email_from_template`). Use this when the user explicitly "
        "asks to 'save a template' / 'create a template' / 'add this to "
        "templates'. Use {{variable_name}} placeholders in subject + "
        "body — they get auto-extracted and listed so callers know what "
        "to fill at send time. Example: subject='Invoice {{invoice_id}} "
        "overdue', body='Hi {{first_name}}, INV-{{invoice_id}} for "
        "₹{{amount}} is overdue…'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name":    {"type": "string", "description": "Template name. e.g. 'invoice_reminder'."},
            "subject": {"type": "string", "description": "Email subject. May contain {{variables}}."},
            "body":    {"type": "string", "description": "Email body. May contain {{variables}}."},
        },
        "required": ["name", "subject", "body"],
    },
    handler=_create_template,
    summary_fn=lambda a: f"Save email template '{a.get('name','?')}'",
)


# ── Render (preview only — no send) ────────────────────────────────────────
def _render_template(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import email_templates as _et
    template_id = (args.get("template_id") or "").strip()
    if not template_id:
        raise ValueError("template_id is required")
    rendered = _et.render_template(ctx["business_id"], template_id,
                                    args.get("variables") or {})
    return {"ok": True, "subject": rendered["subject"], "body": rendered["body"]}


register_tool(
    name="render_email_template",
    description=(
        "Preview a template with variable substitution applied. Doesn't send "
        "anything — useful for showing the user what the final email will "
        "look like before they confirm sending."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "template_id": {"type": "string"},
            "variables":   {"type": "object", "description": "Map of variable name → value."},
        },
        "required": ["template_id"],
    },
    handler=_render_template,
    summary_fn=lambda a: f"Render email template {a.get('template_id','?')}",
)


# ── Send (real send via api.email_provider — Resend or Gmail SMTP) ────────
def _send_from_template(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import email_templates as _et
    from api import email_provider as _ep
    if not _ep.is_configured():
        raise RuntimeError(
            "Email is not configured. Set RESEND_API_KEY (recommended) or "
            "GMAIL_USER + GMAIL_APP_PASSWORD in .env."
        )

    template_id = (args.get("template_id") or "").strip()
    to          = (args.get("to") or "").strip()
    if not template_id or not to:
        raise ValueError("template_id and to are both required")

    rendered = _et.render_template(ctx["business_id"], template_id,
                                    args.get("variables") or {})

    _ep.send_email(to=to, subject=rendered["subject"], body=rendered["body"])

    # Mirror as a CRM interaction if there's a contact at this address — same
    # pattern as the regular send_email tool, so the contact's timeline lights up.
    try:
        from api import crm as _crm
        for c in _crm.list_contacts(ctx["business_id"], search=to, limit=5):
            if (c.get("email") or "").strip().lower() == to.lower():
                _crm.create_interaction(ctx["business_id"], ctx["user_id"], {
                    "type":       "email",
                    "subject":    rendered["subject"],
                    "summary":    rendered["body"][:1000],
                    "contact_id": c["id"],
                    "company_id": c.get("company_id"),
                })
                break
    except Exception as e:
        logger.warning(f"[email_template_tools] CRM interaction log failed for {to}: {e}")

    return {
        "ok":          True,
        "to":          to,
        "subject":     rendered["subject"],
        "template_id": template_id,
        "message":     f"Sent template email to {to}.",
    }


register_tool(
    name="send_email_from_template",
    description=(
        "Send an email by filling a saved template with per-recipient variables. "
        "Use this for repeatable outreach (invoice reminders, welcome emails, "
        "festival promos) instead of redrafting the same copy each time. "
        "Always requires approval — external-facing send, real consequences."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "template_id": {"type": "string", "description": "Email template id (et-…)"},
            "to":          {"type": "string", "description": "Recipient email address."},
            "variables":   {
                "type": "object",
                "description": (
                    "Map of variable name → value. Use list_email_templates "
                    "or render_email_template to find out what variables a "
                    "given template uses."
                ),
            },
        },
        "required": ["template_id", "to"],
    },
    handler=_send_from_template,
    summary_fn=lambda a: f"Email template {a.get('template_id','?')} → {a.get('to','?')}",
    requires_approval=True,  # external-facing send, mirror send_email's gating
)
