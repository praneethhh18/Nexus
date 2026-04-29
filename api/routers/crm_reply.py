"""
AI-drafted reply to a prospect's incoming message.

Sibling of `crm_drafts.draft_outreach` — but where that one writes a fresh
cold outreach, this one writes a *response* to something the prospect said.
The two prompts share scaffolding but differ in what they're asked to do:
the reply drafter has a real previous message to address.

Privacy: prompt sees the prospect's reply text + previous interactions, so
the LLM call runs `sensitive=True` (forced local Ollama).

Output shape:
    {"subject": "<Re: ... or new line>", "body": "<3–6 short paragraphs>"}
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api import crm as _crm
from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke

router = APIRouter(tags=["crm-reply"])


_SYSTEM = """You write short, focused email replies to prospects on behalf \
of a small B2B sales team. The user pastes the prospect's incoming message; \
you write the response.

Rules:
  - Address every concrete point or question they raised — name them.
  - 70–140 words. Three to six short paragraphs. No fluff.
  - Subject line: prefix with "Re: " if there's a clear thread topic, else
    write a fresh 6-word subject. No emojis.
  - Match their tone — warm gets warm, formal gets formal.
  - End with a clear ask or next step (a call, a doc, a confirmation).
  - Sign off "— You". The sender will swap to their own name.
  - Never invent facts. If they ask for something we can't promise (e.g.
    a discount, a feature) say "let me check and come back to you".

Output PRECISELY in this format on a single line, JSON only:

  {"subject": "<line>", "body": "<full body with \\n line breaks>"}

No code fences. No prose before or after.
"""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class ReplyDraftIn(BaseModel):
    incoming_text: str = Field(..., min_length=10, max_length=20000,
                                description="The prospect's message we're replying to.")


def _build_prompt(contact: Dict, company: Optional[Dict],
                  interactions: List[Dict], incoming: str) -> str:
    full_name = " ".join(filter(None, [contact.get("first_name"), contact.get("last_name")])).strip() or "(unnamed)"
    parts = [f"PROSPECT: {full_name}"]
    if contact.get("title"):
        parts.append(f"  Title: {contact['title']}")
    if company:
        line = f"  Company: {company.get('name', '')}"
        if company.get("industry"):
            line += f" — {company['industry']}"
        parts.append(line)

    if interactions:
        parts.append("")
        parts.append("RECENT TOUCHES (newest first, max 4):")
        for it in interactions[:4]:
            kind = it.get("type", "note")
            subj = (it.get("subject") or "(no subject)")[:80]
            summ = (it.get("summary") or "")[:160]
            parts.append(f"  [{kind}] {subj}" + (f" — {summ}" if summ else ""))

    parts.extend([
        "",
        "PROSPECT'S INCOMING MESSAGE (this is what you are replying to):",
        "---",
        incoming.strip(),
        "---",
        "",
        "Write the reply now. JSON only.",
    ])
    return "\n".join(parts)


def _parse_reply(raw: str) -> Optional[Dict[str, str]]:
    if not raw:
        return None
    m = _JSON_RE.search(raw)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    subject = str(obj.get("subject") or "").strip()
    body = str(obj.get("body") or "").strip()
    if not subject or not body:
        return None
    return {"subject": subject[:200], "body": body[:5000]}


def _fallback_reply(prospect_name: str) -> Dict[str, str]:
    """When parsing fails, give the user something they can edit instead of an empty modal."""
    return {
        "subject": "Following up",
        "body": (
            f"Hi {prospect_name or 'there'},\n\n"
            "Thanks for getting back to me. Let me reply on each of your points and "
            "share next steps below. Quick clarifying question first: what's the "
            "best timeline that works for you?\n\n"
            "Happy to set up a 15-minute call if that's easier — let me know.\n\n— You"
        ),
    }


@router.post("/api/crm/contacts/{contact_id}/draft-reply")
def draft_reply_api(
    contact_id: str,
    payload: ReplyDraftIn,
    ctx: dict = Depends(get_current_context),
):
    """
    Draft a contextual response to the prospect's incoming message.
    Tenant-isolated: `crm.get_contact` 404s on cross-tenant access.
    """
    business_id = ctx["business_id"]
    contact = _crm.get_contact(business_id, contact_id)  # 404 on cross-tenant

    company = None
    if contact.get("company_id"):
        try:
            company = _crm.get_company(business_id, contact["company_id"])
        except Exception:
            company = None

    interactions = _crm.list_interactions(business_id, contact_id=contact_id, limit=8)
    full_name = " ".join(filter(None, [contact.get("first_name"), contact.get("last_name")])).strip() or "there"

    prompt = _build_prompt(contact, company, interactions, payload.incoming_text)
    try:
        raw = llm_invoke(
            prompt, system=_SYSTEM, max_tokens=600, temperature=0.4,
            sensitive=True,
        )
    except Exception as e:
        logger.warning(f"[ReplyDraft] LLM call failed for contact {contact_id}: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    parsed = _parse_reply(raw)
    if not parsed:
        logger.warning(f"[ReplyDraft] LLM output didn't parse; using fallback")
        parsed = _fallback_reply(full_name)

    return parsed
