"""
Grounding validator — catches LLM hallucinations before they reach the user.

The LLM agent has tools that produce structured data (contacts, deals,
invoices, etc.) and is told to never fabricate. But system-prompt rules
are advisory; the model sometimes still invents names ("John Doe"),
emails, or numbers.

This module is the hard guardrail:
  1. Collect every "fact value" from the tool results executed THIS turn
     (names, emails, phone numbers, IDs).
  2. After the LLM produces its final answer, extract candidate facts
     from the answer (regex for email + phone, capitalised-word pairs
     for names).
  3. Anything in the answer that's NOT present in the tool evidence is
     flagged. The agent loop logs a warning and appends a transparency
     note to the user.

Design choices:
  - We don't block delivery. False positives are real (legitimate
    generic phrases, prior-conversation references). Better to warn
    the user and ship than to silently lose the answer.
  - We're forgiving on names — only flag 2-word Title Case sequences
    that look like personal names. Single Title-Case words (likely
    nouns/places) are skipped.
  - Numbers (counts, prices) are NOT validated — they're computed,
    not memorised, so the LLM can legitimately derive new ones.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable, List, Set, Tuple

# Email: standard, case-insensitive.
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone: tolerant — captures +91 9XXXXXXXXX, (XXX) XXX-XXXX, etc.
# Min 7 digits to avoid sweeping random numbers.
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}")
# Two-word Title Case sequences: "John Doe", "Sneha Kapoor". Single
# Title-Case words are excluded — they're usually proper nouns from the
# domain (Pro, India, Mumbai) that don't need to live in the tool data.
_NAME_RE = re.compile(r"\b([A-Z][a-z]{1,15})\s+([A-Z][a-z]{1,15})\b")

# Words that look like names but are common false positives — skip them.
_NAME_STOPWORDS: Set[str] = {
    "Hi", "Hello", "Hey", "Dear", "Thanks", "Thank", "Best", "Regards",
    "Sincerely", "Cheers", "Kind", "Warm",
    "I", "You", "We", "They", "It", "He", "She",
    "AI", "AI Agent", "Privacy Mode", "Business Profile", "Cloud LLM",
    "Atlas", "Vox", "Inbox", "Kira", "Sage", "Forge", "Echo", "Memory",
    "Pro", "Starter", "Free",
}


def _walk_facts(value: Any, out: Set[str]) -> None:
    """Flatten nested dict/list values into a set of lowercased strings.

    Numbers are stringified; small ones (<1000) are skipped because
    'we have 5 contacts' shouldn't have to come from the tool dump."""
    if value is None:
        return
    if isinstance(value, str):
        s = value.strip()
        if s:
            out.add(s.lower())
        return
    if isinstance(value, (int, float)):
        if abs(value) >= 1000:
            out.add(str(value).lower())
        return
    if isinstance(value, dict):
        for v in value.values():
            _walk_facts(v, out)
        return
    if isinstance(value, list):
        for v in value:
            _walk_facts(v, out)
        return


def collect_evidence(tool_results: Iterable[Any]) -> Set[str]:
    """Build the universe of values the LLM could legitimately quote.

    Includes every leaf string and large number from every tool result
    in this turn, lowercased."""
    out: Set[str] = set()
    for r in tool_results:
        try:
            _walk_facts(r, out)
        except Exception:
            # Bad shapes shouldn't break the validator.
            pass
    return out


def _name_in_evidence(name: str, evidence: Set[str]) -> bool:
    """A name is grounded if any evidence string contains it (case-insensitive).
    'Sneha Kapoor' matches 'sneha kapoor' or 'Sneha Kapoor — Placement Coordinator'."""
    n = name.lower()
    return any(n in e for e in evidence)


def _email_in_evidence(email: str, evidence: Set[str]) -> bool:
    e = email.lower()
    return any(e in s for s in evidence)


def _phone_normalize(p: str) -> str:
    return re.sub(r"[^\d]", "", p)


def _phone_in_evidence(phone: str, evidence: Set[str]) -> bool:
    digits = _phone_normalize(phone)
    if len(digits) < 7:
        return True   # too short to be a real phone — skip
    return any(digits in _phone_normalize(e) for e in evidence)


def find_ungrounded(answer: str, evidence: Set[str]) -> List[Tuple[str, str]]:
    """Return [(kind, value), ...] for any concrete value in `answer`
    that is NOT supported by the evidence. kind ∈ {name, email, phone}."""
    if not answer:
        return []
    suspects: List[Tuple[str, str]] = []

    for m in _EMAIL_RE.finditer(answer):
        e = m.group(0)
        if not _email_in_evidence(e, evidence):
            suspects.append(("email", e))

    for m in _PHONE_RE.finditer(answer):
        p = m.group(0)
        if not _phone_in_evidence(p, evidence):
            suspects.append(("phone", p))

    for m in _NAME_RE.finditer(answer):
        name = f"{m.group(1)} {m.group(2)}"
        if m.group(1) in _NAME_STOPWORDS or m.group(2) in _NAME_STOPWORDS:
            continue
        if not _name_in_evidence(name, evidence):
            suspects.append(("name", name))

    # Deduplicate while preserving order.
    seen: Set[Tuple[str, str]] = set()
    unique: List[Tuple[str, str]] = []
    for s in suspects:
        key = (s[0], s[1].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)
    return unique


def hedge_message(suspects: List[Tuple[str, str]]) -> str:
    """A short, honest footer explaining which values couldn't be verified.
    Empty string if nothing flagged."""
    if not suspects:
        return ""
    parts = ", ".join(f"`{v}`" for _, v in suspects[:4])
    extra = "" if len(suspects) <= 4 else f" (and {len(suspects) - 4} more)"
    return (
        f"\n\n> ⚠️ I couldn't verify {parts}{extra} against your actual data. "
        f"Treat with caution — these may be guesses."
    )
