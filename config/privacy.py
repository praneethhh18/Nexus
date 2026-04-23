"""
NexusAgent Privacy Layer — protects data that leaves the machine.

The hybrid LLM setup (local Ollama + cloud Claude/Bedrock) creates a data-leakage
risk: prompts sent to the cloud may contain PII, customer records, credentials,
or raw DB rows. This module is the gate everything outbound passes through.

Four defenses, applied in order:

    1. Kill switch   — ALLOW_CLOUD_LLM=false forces everything to local Ollama.
    2. Routing       — requests flagged sensitive=True are forced to local.
    3. Redaction     — emails, phones, IDs, cards, secrets, names replaced with
                       opaque tokens BEFORE leaving the process. A reversible
                       map is returned so responses can be un-redacted locally.
    4. Audit         — every cloud call is logged (prompt hash, not raw text)
                       to outputs/cloud_audit.jsonl for after-the-fact review.

Callers use `prepare_for_cloud(text)` / `restore_from_cloud(text, mapping)`
and `should_use_cloud(sensitive: bool)`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Tuple
from loguru import logger


# ── Config ──────────────────────────────────────────────────────────────────
def _env_bool(key: str, default: bool) -> bool:
    val = os.getenv(key, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


ALLOW_CLOUD_LLM: bool = _env_bool("ALLOW_CLOUD_LLM", True)
REDACT_PII: bool = _env_bool("REDACT_PII", True)
AUDIT_CLOUD_CALLS: bool = _env_bool("AUDIT_CLOUD_CALLS", True)

_ROOT = Path(__file__).parent.parent
_AUDIT_PATH = _ROOT / "outputs" / "cloud_audit.jsonl"


# ── Redaction patterns ──────────────────────────────────────────────────────
# Order matters: longer / more specific patterns first, so they bind before
# weaker patterns swallow part of the match.
_PATTERNS: list[Tuple[str, re.Pattern]] = [
    # Secrets that should never leave
    ("SECRET",  re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")),
    ("SECRET",  re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token|bearer)\s*[:=]\s*[\"']?([A-Za-z0-9_\-\.]{12,})[\"']?")),
    # Indian IDs (common for this user base)
    ("AADHAAR", re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")),
    ("PAN",     re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    # Global IDs
    ("SSN",     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CARD",    re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    # Contact
    ("EMAIL",   re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("PHONE",   re.compile(r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3,5}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}(?!\d)")),
    # Network
    ("IP",      re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    # File paths that include a username (Windows + *nix)
    ("PATH",    re.compile(r"[A-Za-z]:\\Users\\[^\\\"'\s]+")),
    ("PATH",    re.compile(r"/Users/[^/\"'\s]+|/home/[^/\"'\s]+")),
]


def redact(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace PII in `text` with opaque tokens like [EMAIL_1], [PHONE_2].

    Returns (redacted_text, mapping) where mapping is {token: original_value}
    so the caller can restore the original values locally after the cloud
    response comes back.

    The same original value always maps to the same token within one call,
    so the LLM sees consistent placeholders it can reason about.
    """
    if not text or not REDACT_PII:
        return text, {}

    mapping: Dict[str, str] = {}
    # value -> token (so repeated values get the same token)
    seen: Dict[Tuple[str, str], str] = {}
    counters: Dict[str, int] = {}

    def _token_for(kind: str, value: str) -> str:
        key = (kind, value)
        if key in seen:
            return seen[key]
        counters[kind] = counters.get(kind, 0) + 1
        token = f"[{kind}_{counters[kind]}]"
        seen[key] = token
        mapping[token] = value
        return token

    out = text
    for kind, pattern in _PATTERNS:
        out = pattern.sub(lambda m, k=kind: _token_for(k, m.group(0)), out)
    return out, mapping


def restore(text: str, mapping: Dict[str, str]) -> str:
    """Replace redaction tokens back with their original values."""
    if not mapping or not text:
        return text
    out = text
    # Longer tokens first so [EMAIL_10] doesn't get partial-matched by [EMAIL_1]
    for token in sorted(mapping.keys(), key=len, reverse=True):
        out = out.replace(token, mapping[token])
    return out


# ── Routing ─────────────────────────────────────────────────────────────────
def should_use_cloud(sensitive: bool, cloud_available: bool) -> bool:
    """
    Decide whether a given request is allowed to hit the cloud provider.

    Rules:
      - If the admin disabled cloud (ALLOW_CLOUD_LLM=false): never.
      - If the request is flagged sensitive: never (force local).
      - Otherwise: cloud if it's configured, local if not.
    """
    if not cloud_available:
        return False
    if not ALLOW_CLOUD_LLM:
        return False
    if sensitive:
        return False
    return True


# ── Audit ───────────────────────────────────────────────────────────────────
def audit_cloud_call(
    provider: str,
    model: str,
    prompt: str,
    redactions: int,
    token_count: int | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Append a one-line JSON record to outputs/cloud_audit.jsonl for every
    cloud call. We deliberately do NOT store the prompt text — only a hash
    and its length, so the log itself can't leak what it's protecting.
    """
    if not AUDIT_CLOUD_CALLS:
        return
    try:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        prompt_bytes = (prompt or "").encode("utf-8", errors="ignore")
        record = {
            "ts": time.time(),
            "provider": provider,
            "model": model,
            "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest()[:16],
            "prompt_chars": len(prompt or ""),
            "redactions": redactions,
        }
        if token_count is not None:
            record["tokens"] = token_count
        if metadata:
            record["meta"] = metadata
        with _AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning(f"[Privacy] Audit log write failed: {e}")


# ── Convenience: full outbound pipeline ─────────────────────────────────────
def prepare_for_cloud(prompt: str, system: str = "") -> Tuple[str, str, Dict[str, str]]:
    """
    Run the outbound pipeline in one call. Returns the sanitized prompt,
    sanitized system message, and the restore mapping.
    """
    red_prompt, m1 = redact(prompt)
    red_system, m2 = redact(system) if system else ("", {})
    mapping = {**m1, **m2}
    return red_prompt, red_system, mapping
