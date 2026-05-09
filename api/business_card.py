"""Smart business-card scanner — image bytes → structured contact dict.

Uses Amazon Bedrock Nova Lite (vision-capable, cheap, fast — ~$0.0001/card)
because:
    - User already has AWS credentials wired up via llm_bedrock
    - Nova handles image+text natively in the Converse API
    - Lite tier is plenty for OCR-style structured extraction; saves money

Sample WhatsApp interaction this enables:
    User: [snaps photo of business card] [sends to NexusAgent bot]
    Bot:  Created contact: Rohan Mehta, CEO @ Acme Industries
          📞 +91 98765 43210 · ✉ rohan@acme.in
          [tagged 'business-card', source 'whatsapp']

Falls back gracefully if Bedrock isn't configured — returns a friendly
error instead of crashing, so the WhatsApp inbound handler can still tell
the user what's wrong.
"""
from __future__ import annotations

import base64
import json
import os
import re
from typing import Any, Dict, Optional

from loguru import logger


_EXTRACTION_PROMPT = (
    "Look at this business card image and extract contact details. "
    "Reply ONLY with valid JSON in this exact shape — no markdown, no commentary:\n"
    "{\n"
    '  "first_name": "string or null",\n'
    '  "last_name":  "string or null",\n'
    '  "title":      "string or null (job title)",\n'
    '  "company":    "string or null",\n'
    '  "phone":      "string or null (E.164 if visible)",\n'
    '  "email":      "string or null",\n'
    '  "website":    "string or null",\n'
    '  "address":    "string or null",\n'
    '  "confidence": "high|medium|low"\n'
    "}\n\n"
    "Rules:\n"
    "- If the image is not a business card (e.g. it's a document, screenshot, "
    'meme), set confidence to "low" and leave fields null.\n'
    "- Don't invent fields. Anything not clearly visible: null.\n"
    "- Phone numbers: prefer E.164 (+CC). Indian 10-digit numbers: prefix +91."
)


def _detect_image_format(image_bytes: bytes) -> str:
    """Best-effort sniff of common image formats from magic bytes."""
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if image_bytes[:4] == b"GIF8":
        return "gif"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "webp"
    # Bedrock Converse accepts jpeg/png/gif/webp — default to jpeg, the most
    # common WhatsApp camera format.
    return "jpeg"


def extract_business_card(image_bytes: bytes) -> Dict[str, Any]:
    """Vision LLM call → structured contact dict.

    Raises RuntimeError if cloud is unconfigured. Returns a dict with
    `confidence` so the caller can decide whether to auto-create the contact
    or surface for manual review.
    """
    if not (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")):
        raise RuntimeError(
            "Business-card scanning needs Bedrock — AWS credentials aren't set in .env."
        )

    try:
        import boto3
    except ImportError:
        raise RuntimeError("boto3 is not installed; can't reach Bedrock.")

    region = os.getenv("AWS_REGION", "us-east-1")
    # Lite is the cheap, fast vision tier. Pro for higher accuracy if Lite struggles.
    model_id = os.getenv("BEDROCK_VISION_MODEL_ID",
                          os.getenv("BEDROCK_FAST_MODEL_ID", "us.amazon.nova-lite-v1:0"))

    img_format = _detect_image_format(image_bytes)

    client = boto3.client("bedrock-runtime", region_name=region)
    try:
        resp = client.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [
                    {"image": {"format": img_format,
                                "source": {"bytes": image_bytes}}},
                    {"text": _EXTRACTION_PROMPT},
                ],
            }],
            inferenceConfig={"maxTokens": 600, "temperature": 0.1},
        )
    except Exception as e:
        logger.warning(f"[business_card] Bedrock vision call failed: {e}")
        raise RuntimeError(f"Vision LLM call failed: {e}")

    # Pull the text out of the response
    text = ""
    try:
        text = resp["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        logger.warning(f"[business_card] unexpected Bedrock response shape: {resp}")
        raise RuntimeError("Vision LLM gave an unparseable response.")

    # Strip ```json fences just in case the model added them
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(),
                  flags=re.MULTILINE | re.IGNORECASE)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"[business_card] JSON parse failed: {e}; raw: {text[:300]!r}")
        raise RuntimeError("Vision LLM didn't return valid JSON.")

    # Normalise
    out = {
        "first_name": _clean(parsed.get("first_name"), 80),
        "last_name":  _clean(parsed.get("last_name"), 80),
        "title":      _clean(parsed.get("title"), 120),
        "company":    _clean(parsed.get("company"), 200),
        "phone":      _normalize_phone(_clean(parsed.get("phone"), 40)),
        "email":      _clean_email(parsed.get("email")),
        "website":    _clean(parsed.get("website"), 200),
        "address":    _clean(parsed.get("address"), 500),
        "confidence": (parsed.get("confidence") or "low").strip().lower(),
    }
    if out["confidence"] not in ("high", "medium", "low"):
        out["confidence"] = "low"
    return out


def _clean(v: Optional[str], max_len: int) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("null", "none", "n/a"):
        return None
    return s[:max_len]


def _clean_email(v: Optional[str]) -> Optional[str]:
    s = _clean(v, 200)
    if not s:
        return None
    # Loose validity — must look like an email
    if "@" not in s or "." not in s.split("@")[-1]:
        return None
    return s.lower()


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Lightweight E.164-ish coercion. Mirrors voice_tools / lead_hunter helpers."""
    if not phone:
        return None
    s = re.sub(r"[^\d+]", "", phone)
    if not s:
        return None
    if s.startswith("+") and len(s) >= 9:
        return s
    if len(s) == 10:                       # bare Indian mobile
        return "+91" + s
    if len(s) == 12 and s.startswith("91"):
        return "+" + s
    if len(s) == 11 and s.startswith("0"):  # leading-zero local format
        return "+91" + s[1:]
    if len(s) >= 8:
        return "+" + s
    return None


def create_contact_from_extraction(*, business_id: str, user_id: str,
                                    extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Persist the extracted data as a CRM contact. Tagged 'business-card'
    so users can find these later via the existing TagFilterBar."""
    from api import crm as _crm

    fname = extracted.get("first_name") or "Card"
    payload: Dict[str, Any] = {
        "first_name": fname,
        "last_name":  extracted.get("last_name"),
        "phone":      extracted.get("phone") or "",
        "email":      extracted.get("email") or "",
        "title":      extracted.get("title") or "",
        "tags":       "business-card",
        "notes":      _build_notes_block(extracted),
        "source":     "whatsapp-card",
    }
    return _crm.create_contact(business_id, user_id, payload)


def _build_notes_block(extracted: Dict[str, Any]) -> str:
    """Stash company/website/address in the notes field. The CRM doesn't have
    dedicated columns for those on contacts, so notes is the catch-all."""
    parts = ["Imported from business card scan via WhatsApp."]
    if extracted.get("company"):
        parts.append(f"Company: {extracted['company']}")
    if extracted.get("website"):
        parts.append(f"Website: {extracted['website']}")
    if extracted.get("address"):
        parts.append(f"Address: {extracted['address']}")
    if extracted.get("confidence"):
        parts.append(f"Scan confidence: {extracted['confidence']}")
    return "\n".join(parts)
