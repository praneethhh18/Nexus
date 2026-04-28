"""
Capture a lead from a pasted email.

The "magic inbox" pattern (a unique forwarder address per workspace) doesn't
fit a local-first product — it'd require DNS + a public SMTP receiver. Most
small teams happily paste forwarded emails into a textarea instead, which
works on day one with zero infrastructure.

Flow:
  1. User opens CRM → Leads → "Capture from email", pastes the raw email
     (forwarded chain or single message — the LLM handles both).
  2. The extractor pulls structured fields: sender name + email + company,
     a one-line summary of what they want, and the original subject.
  3. We dedup on email (same pattern as the public-form path), create a
     contact tagged `source='email_paste'`, log the original as the first
     interaction, and auto-score against the workspace ICP.

Privacy: the prompt sees full email content (sender + body), so the LLM
call runs `sensitive=True` — forced local Ollama.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api import crm as _crm
from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke
from config.settings import DB_PATH

router = APIRouter(tags=["email-capture"])


_SYSTEM = """You extract structured contact information from one pasted email. \
The email may be a forwarded chain, a single message, a customer reply, or a \
support request. Identify the *original sender* (not the user who forwarded it).

Output ONLY a JSON object on a single line, this exact shape:

  {"sender_name": "<first + last or empty>",
   "sender_email": "<email address or empty>",
   "sender_company": "<company name or empty>",
   "subject": "<original subject line or empty>",
   "summary": "<one sentence summarising what they want>"}

Rules:
  - If you can't find a field, set it to "" — never invent.
  - "sender_name" is the human's full name from the email signature or
    From: header, NOT the user's own name.
  - "summary" is your own short paraphrase. 18 words max. No "Hi" / "Dear".
  - Output only the JSON. No code fences. No prose before or after.
"""


_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


class EmailPasteIn(BaseModel):
    raw_email: str = Field(..., min_length=10, max_length=20000)
    # Optional manual override — if the user knows better than the model.
    override_email: Optional[str] = Field(None, max_length=200)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_extraction(raw: str) -> Optional[Dict]:
    """Return the parsed dict or None on failure."""
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
    return {
        "sender_name":    str(obj.get("sender_name") or "").strip()[:200],
        "sender_email":   str(obj.get("sender_email") or "").strip().lower()[:200],
        "sender_company": str(obj.get("sender_company") or "").strip()[:200],
        "subject":        str(obj.get("subject") or "").strip()[:200],
        "summary":        str(obj.get("summary") or "").strip()[:500],
    }


# Validate-only fallback so a totally garbage LLM output still returns
# *something* — we just leave fields blank for the user to fill in.
def _trivial_extract(raw_email: str) -> Dict:
    """Best-effort regex-based extraction. Used as fallback when the LLM
    output didn't parse — better than 'sorry' for the user."""
    name, email = "", ""
    # "From: Priya Sharma <priya@acme.com>" or "<priya@acme.com>"
    m = re.search(r"From:\s*([^<\n]+?)\s*<\s*([^>\s]+@[^>\s]+)\s*>", raw_email, re.IGNORECASE)
    if m:
        name = m.group(1).strip().strip('"').strip("'")
        email = m.group(2).strip().lower()
    else:
        m = re.search(r"From:\s*([^\s<]+@[^\s<]+)", raw_email, re.IGNORECASE)
        if m:
            email = m.group(1).strip().lower()
    subject = ""
    m = re.search(r"Subject:\s*(.+)", raw_email)
    if m:
        subject = m.group(1).strip()[:200]
    return {
        "sender_name": name, "sender_email": email,
        "sender_company": "", "subject": subject, "summary": "",
    }


@router.post("/api/crm/leads/extract-email")
def extract_email(payload: EmailPasteIn, ctx: dict = Depends(get_current_context)):
    """
    Run the extraction pass without persisting anything. Lets the UI show
    a preview the user can edit before saving.
    """
    try:
        raw = llm_invoke(
            payload.raw_email, system=_SYSTEM, max_tokens=300,
            temperature=0.1, sensitive=True,
        )
    except Exception as e:
        logger.warning(f"[EmailPaste] LLM call failed: {e}")
        # Fall through to regex fallback so the UI is never empty.
        return {**_trivial_extract(payload.raw_email), "fallback": True}

    parsed = _parse_extraction(raw)
    if not parsed:
        logger.warning(f"[EmailPaste] LLM output didn't parse, using fallback")
        return {**_trivial_extract(payload.raw_email), "fallback": True}

    # If the user supplied an override email, honor it.
    if payload.override_email:
        parsed["sender_email"] = payload.override_email.strip().lower()
    return {**parsed, "fallback": False}


class EmailPasteSaveIn(BaseModel):
    raw_email: str = Field(..., min_length=10, max_length=20000)
    sender_name: str = Field("", max_length=200)
    sender_email: str = Field("", max_length=200)
    sender_company: str = Field("", max_length=200)
    subject: str = Field("", max_length=200)
    summary: str = Field("", max_length=500)


@router.post("/api/crm/leads/from-email")
def save_from_email(payload: EmailPasteSaveIn, ctx: dict = Depends(get_current_context)):
    """
    Persist the (possibly user-edited) extraction as a contact + interaction
    + auto-score. Mirrors the public-form intake's dedup + scoring logic.
    """
    business_id = ctx["business_id"]
    user_id = ctx["user"]["id"]

    name = payload.sender_name.strip()
    email = payload.sender_email.strip().lower()
    company_name = payload.sender_company.strip()
    subject = payload.subject.strip()
    summary = payload.summary.strip()

    if not name and not email:
        raise HTTPException(400, "Need at least a sender name or email to capture this lead.")

    # Dedup on email (same pattern as the public form).
    existing_id = None
    if email:
        for c in _crm.list_contacts(business_id, search=email, limit=10):
            if (c.get("email") or "").lower() == email:
                existing_id = c["id"]
                break

    deduped = bool(existing_id)
    if existing_id:
        contact_id = existing_id
    else:
        first, _, last = name.partition(" ")
        contact = _crm.create_contact(business_id, user_id, {
            "first_name": first.strip(),
            "last_name":  last.strip(),
            "email":      email,
        })
        contact_id = contact["id"]
        # Stamp the source — `create_contact` doesn't accept it directly.
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE nexus_contacts SET source = ? WHERE id = ?",
                ("email_paste", contact_id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"[EmailPaste] source stamp failed: {e}")

    # Log the email as a first interaction so the conversation history is intact.
    try:
        _crm.create_interaction(business_id, user_id, {
            "type": "email",
            "subject": subject or "Captured email",
            "summary": (summary + ("\n\n--- ORIGINAL ---\n" + payload.raw_email[:5000]
                                    if payload.raw_email else "")).strip(),
            "contact_id": contact_id,
        })
    except Exception as e:
        logger.warning(f"[EmailPaste] interaction log failed: {e}")

    # Auto-score against the ICP, same as public form intake (best-effort).
    if not deduped:
        try:
            from api.routers.lead_scoring import auto_score_silently
            auto_score_silently(business_id, contact_id)
        except Exception as e:
            logger.debug(f"[EmailPaste] auto-score skipped: {e}")

    # Optionally attach the company. We don't auto-create companies here —
    # too much guesswork. The user can link one from the contact detail page.
    _ = company_name

    return {
        "ok": True,
        "contact_id": contact_id,
        "deduped": deduped,
    }
