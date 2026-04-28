"""
AI-drafted outreach for CRM contacts.

Generates three email variants (warm / professional / direct) per call.
Lives in its own module so the prompt + parsing logic is testable
without standing up the full FastAPI app.

Privacy posture:
  - The prompt includes contact name, email, role, company name, and a
    summary of recent interactions. That's customer data. We pass
    `sensitive=True` to `llm_provider.invoke()` which forces the
    request to stay on local Ollama — see `config/privacy.py`.
  - The output never echoes raw stored values; the LLM may use them in
    the body but that's the user's intent (we want personalised drafts).
  - On parse failure we return a generic single-variant fallback so the
    UI is never empty; the user can regenerate.

Output shape (stable contract — frontend depends on this):
    {
      "variants": [
        { "tone": "warm" | "professional" | "direct",
          "subject": "...",
          "body":    "..." }
      ]
    }
"""
from __future__ import annotations

import re
from typing import Dict, List

from fastapi import HTTPException
from loguru import logger

from api import crm as _crm
from config.llm_provider import invoke as llm_invoke


_TONES = ("warm", "professional", "direct")

_SYSTEM = """You are an outreach copywriter for a small B2B sales team. \
You write three short, personalised email variants for the contact described \
in the prompt. Each variant has a different tone:
  - "warm"        — friendly, light, references something specific.
  - "professional"— direct, value-focused, shorter.
  - "direct"      — concise, asks for a 15-minute call explicitly.

Rules:
  - 60–110 words per body. Never longer.
  - One concrete reason for the outreach. No fluff openers like "I hope you're doing well".
  - Subject lines: under 8 words, no emojis, no clickbait.
  - Sign off "— You". The sender will swap to their own name.
  - Output PRECISELY in this format, three blocks back-to-back:

VARIANT: warm
SUBJECT: <subject>
BODY:
<body lines, may span multiple lines>

VARIANT: professional
SUBJECT: <subject>
BODY:
<body lines>

VARIANT: direct
SUBJECT: <subject>
BODY:
<body lines>
"""


def _build_context(business_id: str, contact_id: str) -> Dict:
    """Pull contact + signals; raises HTTPException(404) on cross-tenant or unknown."""
    contact = _crm.get_contact(business_id, contact_id)  # raises 404 if not found

    company = None
    if contact.get("company_id"):
        try:
            company = _crm.get_company(business_id, contact["company_id"])
        except Exception:
            company = None

    interactions = _crm.list_interactions(business_id, contact_id=contact_id, limit=8)
    # list_deals doesn't filter by contact_id directly — fetch + filter.
    all_deals = _crm.list_deals(business_id, limit=200)
    contact_deals = [d for d in all_deals if d.get("contact_id") == contact_id]
    open_deals = [d for d in contact_deals if d.get("stage") not in ("won", "lost")]

    return {
        "contact": contact,
        "company": company,
        "interactions": interactions,
        "open_deals": open_deals,
    }


def _build_prompt(ctx_data: Dict) -> str:
    contact = ctx_data["contact"]
    company = ctx_data["company"]
    full_name = " ".join(filter(None, [contact.get("first_name"), contact.get("last_name")])).strip() or "(unnamed)"

    lines = [
        f"CONTACT: {full_name}",
        f"  Title:   {contact.get('title') or '(unknown)'}",
        f"  Email:   {contact.get('email') or '(none)'}",
    ]
    if company:
        line = f"  Company: {company.get('name')}"
        if company.get("industry"):
            line += f" — {company['industry']}"
        lines.append(line)
        if company.get("size"):
            lines.append(f"  Size:    {company['size']}")
    if contact.get("notes"):
        lines.append(f"  Notes:   {contact['notes'][:280]}")
    if contact.get("source") and contact["source"] != "manual":
        lines.append(f"  Source:  {contact['source']}  (this person came in inbound, not cold)")

    open_deals = ctx_data.get("open_deals") or []
    if open_deals:
        d = open_deals[0]
        lines.append("\nOPEN DEAL with this contact:")
        lines.append(f"  Name:  {d.get('name')}")
        stage_line = f"  Stage: {d.get('stage')}"
        if d.get("value"):
            stage_line += f" · ${d['value']:,}"
        lines.append(stage_line)
        if d.get("notes"):
            lines.append(f"  Notes: {d['notes'][:200]}")

    interactions = ctx_data.get("interactions") or []
    if interactions:
        lines.append("\nRECENT INTERACTIONS (newest first):")
        for it in interactions[:5]:
            kind = it.get("type", "note")
            subj = (it.get("subject") or "").strip() or "(no subject)"
            summ = (it.get("summary") or "").strip()[:160]
            when = (it.get("occurred_at") or it.get("created_at") or "")[:10]
            lines.append(f"  - [{kind} · {when}] {subj}" + (f" — {summ}" if summ else ""))
    else:
        lines.append("\nNO PRIOR INTERACTIONS — this is a first-touch outreach. Don't reference past conversations.")

    return "\n".join(lines)


def _parse_variants(raw: str) -> List[Dict[str, str]]:
    """Split the LLM's output into the three structured variants."""
    raw = (raw or "").strip()
    if not raw:
        return []
    # Split on lines that start with "VARIANT:"
    chunks = re.split(r"(?im)^\s*VARIANT\s*:\s*", raw)
    variants: List[Dict[str, str]] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # First line is the tone; then "SUBJECT: ..." then "BODY:" then body.
        lines = chunk.splitlines()
        if not lines:
            continue
        tone = (lines[0] or "").strip().lower()
        if tone not in _TONES:
            continue
        subject = ""
        body_lines: List[str] = []
        in_body = False
        for ln in lines[1:]:
            if not in_body:
                m = re.match(r"^\s*SUBJECT\s*:\s*(.*)$", ln, re.IGNORECASE)
                if m:
                    subject = m.group(1).strip()
                    continue
                if re.match(r"^\s*BODY\s*:\s*$", ln, re.IGNORECASE):
                    in_body = True
                    continue
                # Some LLMs put BODY: <text> on one line.
                m = re.match(r"^\s*BODY\s*:\s*(.+)$", ln, re.IGNORECASE)
                if m:
                    in_body = True
                    body_lines.append(m.group(1).strip())
                    continue
            else:
                body_lines.append(ln)
        body = "\n".join(body_lines).strip()
        if subject and body:
            variants.append({"tone": tone, "subject": subject, "body": body})
    return variants


def _fallback_variant(contact_name: str) -> Dict[str, str]:
    """Last-resort if parsing failed — keeps the UI from being empty."""
    return {
        "tone": "professional",
        "subject": "Quick intro",
        "body": (
            f"Hi {contact_name or 'there'},\n\n"
            "Reaching out because we help small teams automate their CRM, "
            "invoicing, and document workflows in one place. Worth a 15-minute "
            "call this week to see if it's a fit?\n\n— You"
        ),
    }


def draft_outreach(business_id: str, contact_id: str) -> Dict:
    """Public entry point used by the API route."""
    ctx_data = _build_context(business_id, contact_id)  # 404 if cross-tenant

    contact = ctx_data["contact"]
    full_name = " ".join(filter(None, [contact.get("first_name"), contact.get("last_name")])).strip() or "there"

    prompt = _build_prompt(ctx_data)
    try:
        # `sensitive=True` — forces local Ollama so customer data never leaves.
        raw = llm_invoke(
            prompt, system=_SYSTEM, max_tokens=900, temperature=0.4,
            sensitive=True,
        )
    except Exception as e:
        logger.warning(f"[Drafts] LLM call failed for contact {contact_id}: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    variants = _parse_variants(raw)
    if not variants:
        logger.warning(f"[Drafts] LLM output didn't parse for contact {contact_id}; using fallback")
        variants = [_fallback_variant(full_name)]

    # Ensure all three tones are present even if the LLM dropped one.
    seen = {v["tone"] for v in variants}
    for tone in _TONES:
        if tone not in seen:
            variants.append({**_fallback_variant(full_name), "tone": tone})

    # Stable order: warm → professional → direct.
    order = {t: i for i, t in enumerate(_TONES)}
    variants.sort(key=lambda v: order.get(v["tone"], 99))

    return {"variants": variants}
