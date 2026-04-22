"""
Email Tool — drafts emails with LLM, requires explicit approval, then sends via Gmail SMTP.
Falls back to saving draft files if credentials not configured.
"""
from __future__ import annotations

import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger

from config.settings import (
    GMAIL_USER, GMAIL_APP_PASSWORD, EMAIL_ENABLED, EMAIL_DRAFTS_DIR
)
from config.llm_config import get_llm


def _draft_email(recipient: str, subject_hint: str, context: str,
                 feedback: str = "") -> Dict[str, str]:
    """Use local LLM to draft a professional email."""
    llm = get_llm()

    feedback_line = f"\nUser feedback on previous draft: {feedback}" if feedback else ""
    prompt = f"""Write a professional business email based on the context below.

Recipient: {recipient}
Subject hint: {subject_hint}
Context: {context}{feedback_line}

Format your response EXACTLY like this:
TO: [recipient email]
SUBJECT: [subject line]
BODY:
[email body]

Be professional, concise, and helpful. End with an appropriate sign-off."""

    try:
        response = llm.invoke(prompt)
        lines = response.strip().split("\n")
        to_line = subject_line = ""
        body_lines = []
        in_body = False
        for line in lines:
            if line.upper().startswith("TO:"):
                to_line = line[3:].strip()
            elif line.upper().startswith("SUBJECT:"):
                subject_line = line[8:].strip()
            elif line.upper().startswith("BODY:"):
                in_body = True
            elif in_body:
                body_lines.append(line)
        return {
            "to": to_line or recipient,
            "subject": subject_line or subject_hint,
            "body": "\n".join(body_lines).strip(),
        }
    except Exception as e:
        logger.error(f"[Email] Draft generation failed: {e}")
        return {
            "to": recipient,
            "subject": subject_hint,
            "body": f"[Draft generation failed: {e}]\n\nContext: {context}",
        }


def _send_gmail(to: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP with TLS."""
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to, msg.as_string())

        logger.success(f"[Email] Sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"[Email] Send failed: {e}")
        return False


def _save_draft(draft: Dict[str, str]) -> str:
    """Save email draft to file."""
    Path(EMAIL_DRAFTS_DIR).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = Path(EMAIL_DRAFTS_DIR) / f"draft_{timestamp}.txt"
    content = f"TO: {draft['to']}\nSUBJECT: {draft['subject']}\n\n{draft['body']}"
    fname.write_text(content, encoding="utf-8")
    logger.info(f"[Email] Draft saved: {fname}")
    return str(fname)


def compose_and_send(
    recipient: str,
    subject_hint: str,
    context: str,
    approval_callback=None,
    test_mode: bool = False,
) -> Dict[str, Any]:
    """
    Full email workflow:
    1. Draft email with LLM
    2. Display draft
    3. Request approval via callback (or auto-approve in test_mode)
    4. Send or save draft

    approval_callback: callable(draft_dict) → (approved: bool, feedback: str)
    Returns result dict.
    """
    start = time.time()
    draft = _draft_email(recipient, subject_hint, context)
    feedback = ""
    approved = False

    # Show the draft
    draft_display = (
        f"\n{'='*50}\nEMAIL DRAFT\n{'='*50}\n"
        f"TO: {draft['to']}\n"
        f"SUBJECT: {draft['subject']}\n"
        f"{'─'*50}\n{draft['body']}\n{'='*50}"
    )
    print(draft_display)

    if test_mode:
        approved = False  # In test mode, never actually send
        logger.info("[Email] Test mode — email NOT sent")
    elif approval_callback:
        approved, feedback = approval_callback(draft)
        if not approved and feedback:
            # Regenerate with feedback
            draft = _draft_email(recipient, subject_hint, context, feedback)
            approved, feedback = approval_callback(draft)
    else:
        # Console fallback
        answer = input("\nSend this email? (yes/no): ").strip().lower()
        approved = answer in ("yes", "y")

    duration_ms = int((time.time() - start) * 1000)
    result: Dict[str, Any] = {
        "draft": draft,
        "approved": approved,
        "sent": False,
        "saved_path": None,
        "error": None,
    }

    if approved and EMAIL_ENABLED and not test_mode:
        sent = _send_gmail(draft["to"], draft["subject"], draft["body"])
        result["sent"] = sent
        if not sent:
            result["error"] = "SMTP send failed"
    else:
        saved_path = _save_draft(draft)
        result["saved_path"] = saved_path

    # Audit log
    try:
        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="email_tool",
            input_summary=f"To: {recipient}, Subject hint: {subject_hint}",
            output_summary=f"approved={approved}, sent={result['sent']}",
            duration_ms=duration_ms,
            approved=approved,
            success=result["sent"] or result["saved_path"] is not None,
            error=result.get("error"),
        )
    except Exception:
        pass

    return result
