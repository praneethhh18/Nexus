"""Call-queue bridge — push CRM contacts into the nexuscaller-lab auto-dialer.

Pairs Lead Hunter / Lead Scorer / Outreach with the lab's lead queue (added in
nexuscaller-lab commit 29ee8da). Makes the full top-of-funnel loop work in
one chat command:

    "find catering services in Bengaluru, score them, send the top 10 to
     the auto-dial queue, then start dialing"

Without this bridge the user would have to manually re-add CRM contacts in
the lab UI. This tool POSTs them in bulk via the lab's /api/leads/bulk
endpoint — same schema CSV-import users see.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx
from loguru import logger

from agents.tool_registry import register_tool


def _lab_url() -> str:
    """Reuse the existing LAB_URL env var (already used by voice_tools.dial_contact)."""
    url = (os.getenv("LAB_URL") or os.getenv("VOX_LAB_URL") or "").rstrip("/")
    if not url:
        raise RuntimeError(
            "LAB_URL not configured — set it in .env to the nexuscaller-lab "
            "server URL (e.g. http://localhost:8765)."
        )
    return url


def _push_to_call_queue(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    purpose = (args.get("purpose") or "a quick check-in").strip()[:300]
    max_count = max(1, min(int(args.get("max_count", 25)), 200))

    # Reuse outreach_tools' segment filter — same DSL the user already knows.
    from agents.tools.outreach_tools import _filter_contacts
    segment = args.get("segment") or {}
    if not isinstance(segment, dict):
        raise ValueError("segment must be an object")
    # Phone is required for the auto-dialer to do anything useful
    segment.setdefault("has_phone", True)

    contacts = _filter_contacts(business_id, segment, max_count)
    if not contacts:
        return {
            "ok":      True,
            "matched": 0,
            "queued":  0,
            "message": "No contacts matched that segment. Try loosening the filters.",
        }

    # Lab's /api/leads/bulk wants a list of {phone, name, purpose, ...}
    leads_payload: List[Dict[str, Any]] = [
        {
            "phone":       c.get("phone") or "",
            "name":        " ".join(filter(None, [c.get("first_name"), c.get("last_name")])).strip()
                           or "Lead",
            "purpose":     purpose,
            "notes":       (c.get("notes") or "")[:500],
            "business_id": business_id,
            "contact_id":  c["id"],
        }
        for c in contacts
        if (c.get("phone") or "").strip()
    ]
    if not leads_payload:
        return {
            "ok":      True,
            "matched": len(contacts),
            "queued":  0,
            "message": "Matching contacts have no phone numbers. Add phones first.",
        }

    lab_url = _lab_url()
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(f"{lab_url}/api/leads/bulk",
                             json={"leads": leads_payload})
    except Exception as e:
        raise RuntimeError(f"Lab unreachable at {lab_url}: {e}")

    if r.status_code != 200:
        raise RuntimeError(f"Lab returned HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    queued = int(data.get("added", 0))
    skipped = int(data.get("skipped", 0))

    public_lab = (os.getenv("VOX_PUBLIC_URL") or lab_url).rstrip("/")
    queue_url = f"{public_lab}/leads"

    auto_start = bool(args.get("start_dialer", False))
    started = False
    if auto_start and queued > 0:
        try:
            with httpx.Client(timeout=10.0) as client:
                start_resp = client.post(f"{lab_url}/api/leads/queue/start", json={
                    "telephony_provider": (args.get("telephony_provider") or "twilio"),
                    "delay_sec":          int(args.get("delay_sec", 12)),
                    "callback_url":       (os.getenv("NEXUS_PUBLIC_URL")
                                            or "http://localhost:8000").rstrip("/")
                                          + "/api/voice/callback",
                    "business_id":        business_id,
                    "business_name":      _business_name(business_id),
                })
            started = (start_resp.status_code == 200)
        except Exception as e:
            logger.warning(f"[call_queue_tools] auto-start failed: {e}")

    msg_parts = [f"Queued {queued} contact(s) to the auto-dialer."]
    if skipped:
        msg_parts.append(f"{skipped} skipped (bad phone format).")
    if auto_start:
        msg_parts.append("Auto-dialer started." if started else "Couldn't start auto-dialer (start it manually).")
    msg_parts.append(f"Watch progress: {queue_url}")

    return {
        "ok":          True,
        "matched":     len(contacts),
        "queued":      queued,
        "skipped":     skipped,
        "started":     started,
        "queue_url":   queue_url,
        "message":     " ".join(msg_parts),
    }


def _business_name(business_id: str) -> str:
    try:
        from api.businesses import get_business
        b = get_business(business_id) or {}
        return (b.get("name") or "").strip()
    except Exception:
        return ""


register_tool(
    name="push_to_call_queue",
    description=(
        "Push a segment of CRM contacts into the nexuscaller-lab auto-dialer "
        "queue so the agent calls them one by one. Use after Lead Hunter + "
        "Lead Scorer to call the top N leads in bulk. Set start_dialer=true "
        "to also kick off the dialer immediately. Returns a link to the "
        "live queue UI where the operator can watch progress + see the "
        "good/bad bucketing."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "segment": {
                "type": "object",
                "description": (
                    "Contact filters. Same shape as outreach_campaign's "
                    "segment: tag, source, has_phone, has_email, "
                    "never_contacted, not_contacted_days. has_phone defaults "
                    "to true (auto-dialer needs a phone)."
                ),
                "properties": {
                    "tag":                {"type": "string"},
                    "source":             {"type": "string"},
                    "has_phone":          {"type": "boolean"},
                    "has_email":          {"type": "boolean"},
                    "never_contacted":    {"type": "boolean"},
                    "not_contacted_days": {"type": "integer"},
                },
            },
            "purpose": {
                "type": "string",
                "description": "What the agent should say on each call. Short + concrete.",
            },
            "max_count": {
                "type": "integer",
                "default": 25,
                "description": "Cap on how many to push (1-200). Default 25.",
            },
            "start_dialer": {
                "type": "boolean",
                "default": False,
                "description": "If true, also POST to /api/leads/queue/start to begin dialing immediately.",
            },
            "telephony_provider": {
                "type": "string",
                "enum": ["twilio", "telnyx", "signalwire", "exotel"],
                "default": "twilio",
                "description": "SIP trunk to use when start_dialer=true.",
            },
            "delay_sec": {
                "type": "integer",
                "default": 12,
                "description": "Seconds between calls when start_dialer=true.",
            },
        },
        "required": ["purpose"],
    },
    handler=_push_to_call_queue,
    summary_fn=lambda a: (
        f"Push to call queue ({a.get('purpose','')[:60]}) — "
        f"max {a.get('max_count',25)}"
        + (" + start" if a.get("start_dialer") else "")
    ),
)
