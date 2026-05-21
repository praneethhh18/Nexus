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
# Single Title-Case word — used by find_ungrounded to walk adjacent pairs.
_TITLE_WORD_RE = re.compile(r"\b([A-Z][a-z]{1,15})\b")

# Words that look like names but are common false positives — skip them.
# Two angles: the word lives in a section header/label/UI chrome rather
# than naming a real person OR org, so it doesn't need to live in the
# evidence set. Each membership check is against either of the two words
# in the Title-Case pair, so "Next Steps" matches via "Next" or "Steps".
_NAME_STOPWORDS: Set[str] = {
    # Greetings + sign-offs
    "Hi", "Hello", "Hey", "Dear", "Thanks", "Thank", "Best", "Regards",
    "Sincerely", "Cheers", "Kind", "Warm",
    # Pronouns
    "I", "You", "We", "They", "It", "He", "She",
    # Product nouns / UI chrome
    "AI", "AI Agent", "Privacy Mode", "Business Profile", "Cloud LLM",
    "Atlas", "Vox", "Inbox", "Kira", "Sage", "Forge", "Echo", "Memory",
    "Pro", "Starter", "Free",
    # Section / list headers the agent commonly writes in long answers
    "Next", "Steps", "Key", "Observations", "Summary", "Overview",
    "Recommendation", "Recommendations", "Action", "Actions",
    "Items", "Final", "Verdict", "Notes", "Note", "Important",
    "Highlights", "Insights", "Risks", "Assumptions", "Critique",
    "Conclusion", "Background", "Context", "Reasoning", "Analysis",
    "Plan", "Proposal",
    # Table / form column labels
    "Due", "Date", "Issue", "Total", "Amount", "Subtotal",
    "Invoice", "Number", "Customer", "Name", "First", "Last",
    "Company", "Phone", "Email", "Address", "Postal", "Code",
    "Status", "Priority", "Stage", "Pipeline", "Deal", "Stage",
    "Account", "Type", "Created", "Updated", "Modified",
    "Description", "Quantity", "Unit", "Price", "Tax", "Discount",
    "Currency", "Industry", "Title", "Role", "Department",
    "Last", "Called", "Contact", "Details", "None", "The",
    # Time markers commonly used as headers
    "Today", "Yesterday", "Tomorrow", "Week", "Month", "Year",
    "Q1", "Q2", "Q3", "Q4",
    # Status values + business terms
    "Past", "Due", "Paid", "Unpaid", "Pending", "Draft",
    "Open", "Closed", "Won", "Lost", "Active", "Inactive",
    "Net", "Gross", "Impact", "Revenue", "Profit", "Cost",
    "Lead", "Leads", "Qualified", "Proposal", "Negotiation",
}


def _walk_facts(value: Any, out: Set[str]) -> None:
    """Flatten nested dict/list values into a set of lowercased strings.

    Numbers are stringified; small ones (<1000) are skipped because
    'we have 5 contacts' shouldn't have to come from the tool dump.

    For dicts that look like a contact record (have both first_name +
    last_name), also emit the joined 'first last' form. Otherwise the
    validator flags a legitimate 'Hi Meera Iyer' answer as ungrounded
    because evidence only has 'meera' and 'iyer' as separate strings."""
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
        # Synthesise common name combinations so the validator doesn't
        # false-flag answers that quote a contact's full name.
        f = (value.get("first_name") or "").strip()
        l = (value.get("last_name") or "").strip()
        if f and l:
            out.add(f"{f.lower()} {l.lower()}")
            out.add(f"{l.lower()}, {f.lower()}")  # CRM-style sort key
        # Also handle 'name' field (companies, deals) for cleanliness.
        n = (value.get("name") or "").strip()
        if n:
            out.add(n.lower())
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


def _strip_structural_markdown(answer: str) -> str:
    """Remove markdown structural chrome so the name regex only scans the
    answer's prose. Without this, the validator flags table column
    headers ("Due Date", "Key Observations") and section titles
    ("**Next Steps**") as ungrounded people-names, which scares users
    even though the agent isn't actually claiming those are CRM records."""
    out_lines = []
    for ln in answer.splitlines():
        stripped = ln.strip()
        # Markdown table separator rows: |---|---|
        if re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?", stripped):
            continue
        # Table rows (any line with two or more |) — column labels live here.
        if stripped.count("|") >= 2:
            continue
        # Headings: # H1 / ## H2 / ### H3 + their leading marker
        if stripped.startswith("#"):
            continue
        # Bold-only headers like "**Next Steps**" or "**Key Observations:**"
        if re.fullmatch(r"\**\s*[A-Za-z][\w\s]*\**\s*:?\**", stripped) \
                and stripped.startswith("**") and stripped.rstrip(":").endswith("**"):
            continue
        out_lines.append(ln)
    return "\n".join(out_lines)


def find_ungrounded(answer: str, evidence: Set[str]) -> List[Tuple[str, str]]:
    """Return [(kind, value), ...] for any concrete value in `answer`
    that is NOT supported by the evidence. kind ∈ {name, email, phone}."""
    if not answer:
        return []
    suspects: List[Tuple[str, str]] = []

    # Emails / phones are checked against the FULL answer — they're
    # always factual claims, never section chrome.
    for m in _EMAIL_RE.finditer(answer):
        e = m.group(0)
        if not _email_in_evidence(e, evidence):
            suspects.append(("email", e))

    for m in _PHONE_RE.finditer(answer):
        p = m.group(0)
        if not _phone_in_evidence(p, evidence):
            suspects.append(("phone", p))

    # Names are checked AFTER stripping markdown chrome, because Title-Case
    # pairs inside table column headers + section titles aren't factual
    # claims about CRM records. We use a sliding-window over ALL adjacent
    # Title-Case word pairs (rather than non-overlapping regex matches)
    # so a stopword leading into a real name doesn't mask the name —
    # e.g. "Contact John Doe" checks both (Contact, John) AND (John, Doe).
    name_scan_text = _strip_structural_markdown(answer)
    title_words = list(_TITLE_WORD_RE.finditer(name_scan_text))
    for i in range(len(title_words) - 1):
        w1m, w2m = title_words[i], title_words[i + 1]
        between = name_scan_text[w1m.end():w2m.start()]
        # Words must be separated by whitespace only (so we don't pair
        # "Praneeth" with the next sentence's "The").
        if between.strip() != "" or "\n" in between:
            continue
        w1, w2 = w1m.group(1), w2m.group(1)
        if w1 in _NAME_STOPWORDS or w2 in _NAME_STOPWORDS:
            continue
        name = f"{w1} {w2}"
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
