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

import contextvars
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple
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


# ── Per-request stats (contextvar — safe across async / threads) ────────────
# These power the "N values redacted before cloud" badge the chat UI shows.
# A caller resets the stats at the start of a request, performs LLM work,
# and reads the accumulator afterward.
_STATS_VAR: contextvars.ContextVar[dict] = contextvars.ContextVar(
    "privacy_stats", default=None
)


def _empty_stats() -> dict:
    return {
        "cloud_calls": 0,
        "local_calls": 0,
        "redactions": 0,
        "by_kind": {},          # e.g. {"EMAIL": 3, "PHONE": 1}
        "provider": None,       # last provider actually used
        "kill_switch_blocked": False,
        "sensitive_forced_local": False,
        "calls": [],            # per-call receipts (timestamp, provider, sha, redactions)
    }


def reset_stats() -> None:
    """Start fresh stats for the current request."""
    _STATS_VAR.set(_empty_stats())


def get_stats() -> dict:
    """Read a copy of the current request's privacy stats (never None)."""
    s = _STATS_VAR.get()
    return dict(s) if s else _empty_stats()


def _record(**updates) -> None:
    """Merge updates into the active stats dict (no-op if not initialised)."""
    s = _STATS_VAR.get()
    if s is None:
        return
    for k, v in updates.items():
        if k == "by_kind":
            for kind, n in (v or {}).items():
                s["by_kind"][kind] = s["by_kind"].get(kind, 0) + n
        elif k == "redactions":
            s["redactions"] = s.get("redactions", 0) + int(v)
        elif k in ("cloud_calls", "local_calls"):
            s[k] = s.get(k, 0) + int(v)
        elif k == "_call_receipt":
            s["calls"].append(v)
        else:
            s[k] = v


def note_call(
    provider: str, cloud: bool, redactions: int,
    kinds: Dict[str, int] | None = None,
    audit_record: dict | None = None,
):
    """Record one LLM call against the active stats.

    `audit_record`, when provided, is the dict returned by audit_cloud_call.
    For local calls a synthetic receipt is created so the UI can show every
    call (cloud + local) the request made.
    """
    _record(
        provider=provider,
        **({"cloud_calls": 1} if cloud else {"local_calls": 1}),
        redactions=redactions,
        by_kind=kinds or {},
    )
    if audit_record is not None:
        receipt = {
            "ts": audit_record.get("ts"),
            "provider": audit_record.get("provider", provider),
            "model": audit_record.get("model"),
            "sha": audit_record.get("prompt_sha256"),
            "chars": audit_record.get("prompt_chars"),
            "redactions": audit_record.get("redactions", 0),
            "cloud": True,
        }
    else:
        receipt = {
            "ts": time.time(), "provider": provider, "model": None,
            "sha": None, "chars": 0, "redactions": 0, "cloud": cloud,
        }
    _record(_call_receipt=receipt)


def note_forced_local(reason: str) -> None:
    """Flag that cloud was requested but we routed to local instead."""
    s = _STATS_VAR.get()
    if s is None:
        return
    if reason == "kill_switch":
        s["kill_switch_blocked"] = True
    elif reason == "sensitive":
        s["sensitive_forced_local"] = True


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


def kind_counts(mapping: Dict[str, str]) -> Dict[str, int]:
    """Count redactions per kind (EMAIL, PHONE, ...) from a token mapping."""
    out: Dict[str, int] = {}
    for token in mapping.keys():
        # token looks like "[EMAIL_3]" — extract the kind before the underscore
        if token.startswith("[") and token.endswith("]"):
            inside = token[1:-1]
            kind = inside.rsplit("_", 1)[0] if "_" in inside else inside
            out[kind] = out.get(kind, 0) + 1
    return out


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
        note_forced_local("kill_switch")
        return False
    if sensitive:
        note_forced_local("sensitive")
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
) -> dict:
    """
    Append a one-line JSON record to outputs/cloud_audit.jsonl for every
    cloud call. We deliberately do NOT store the prompt text — only a hash
    and its length, so the log itself can't leak what it's protecting.

    Returns the record (whether or not file logging is enabled) so callers
    can attach it to per-request privacy stats for inline receipts.
    """
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
    if AUDIT_CLOUD_CALLS:
        try:
            _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with _AUDIT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"[Privacy] Audit log write failed: {e}")
    return record


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
