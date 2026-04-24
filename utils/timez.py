"""
Timestamp helpers — one import point so we never drift back to the deprecated
`datetime.utcnow()` pattern.

Python 3.12+ deprecated `datetime.utcnow()` because it returns a naive
datetime that pretends to be UTC, losing timezone information silently. The
replacement is `datetime.now(timezone.utc)` which returns a timezone-aware
UTC datetime.

For historical compatibility, our SQLite rows store naive ISO strings without
the `+00:00` suffix. `now_iso()` strips the tz suffix so we stay wire-compatible
with every existing row; `now_iso_tz()` keeps the suffix when a new callsite
wants the proper tz-aware form.
"""
from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    """Current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def now_iso() -> str:
    """
    Current UTC time as an ISO string without the '+00:00' suffix.

    Matches the format every pre-existing `datetime.utcnow().isoformat()`
    row already uses, so ORDER BY / comparisons across old and new rows
    keep working.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def now_iso_tz() -> str:
    """Current UTC time as a tz-aware ISO string ('...+00:00')."""
    return datetime.now(timezone.utc).isoformat()


def now_utc_naive() -> datetime:
    """
    Current UTC time as a NAIVE datetime (no tzinfo).

    Historically every callsite used `datetime.utcnow()`. This helper is the
    drop-in replacement that keeps naive-datetime semantics so comparisons
    against other naive datetimes (from `datetime.fromisoformat(row_str)`)
    continue to work without raising `TypeError: can't compare offset-naive
    and offset-aware datetimes`.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
