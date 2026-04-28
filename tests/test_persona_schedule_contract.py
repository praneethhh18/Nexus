"""
Persona ↔ scheduler ↔ UI contract.

Three things must stay in lockstep, otherwise we end up with:
  - an agent that's advertised but never runs (declared in DEFAULTS, missing
    from start_agent_scheduler) → invisible no-op
  - an agent that runs in the background but doesn't show up in the UI
    (declared + scheduled, but missing from list_personas order) → spooky
  - a scheduler job-id mismatch that breaks "next run" lookups in the UI

This test enforces all three. Add a new persona = add it to DEFAULTS,
SCHEDULER_JOB_IDS, list_personas order, AND register it in
start_agent_scheduler. Skip any of those = red test.
"""
from __future__ import annotations

import os
import re
import importlib
import tempfile

import pytest

from agents import personas


def _scheduler_source() -> str:
    """Read the scheduler module source so we can grep for registered job-ids
    without actually starting APScheduler (which would need a real DB)."""
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.normpath(os.path.join(here, "..", "agents", "background", "scheduler.py"))
    with open(src, "r", encoding="utf-8") as f:
        return f.read()


def _registered_job_ids() -> set[str]:
    """Pull every `_register("agent-...", ...)` call out of the scheduler source."""
    src = _scheduler_source()
    return set(re.findall(r'_register\(\s*"(agent-[a-z0-9-]+)"', src))


def test_every_persona_has_a_scheduler_job_id_mapping():
    """DEFAULTS keys must be present in SCHEDULER_JOB_IDS — used by the UI
    to show "next run" times."""
    missing = set(personas.DEFAULTS) - set(personas.SCHEDULER_JOB_IDS)
    assert not missing, (
        f"Personas in DEFAULTS but missing from SCHEDULER_JOB_IDS: {missing}. "
        "Add an entry mapping the agent_key to its agent-* scheduler job id."
    )


def test_no_orphan_job_id_mappings():
    """Reverse direction — SCHEDULER_JOB_IDS shouldn't reference personas
    that were renamed or deleted."""
    orphans = set(personas.SCHEDULER_JOB_IDS) - set(personas.DEFAULTS)
    assert not orphans, (
        f"SCHEDULER_JOB_IDS keys missing from DEFAULTS: {orphans}. "
        "Either add the persona to DEFAULTS or remove the mapping."
    )


def test_every_persona_is_actually_scheduled():
    """Every persona's scheduler-job-id must be _register()'d in
    start_agent_scheduler. Otherwise the agent is advertised but inert."""
    registered = _registered_job_ids()
    expected = set(personas.SCHEDULER_JOB_IDS.values())
    not_scheduled = expected - registered
    assert not not_scheduled, (
        f"Personas declared but not registered in start_agent_scheduler: "
        f"{not_scheduled}. Check agents/background/scheduler.py."
    )


def test_every_scheduled_job_has_a_persona():
    """Reverse direction — every agent-* job that runs must be visible in
    the UI. A scheduled-but-hidden job is silent work behind the user's back."""
    registered = _registered_job_ids()
    expected = set(personas.SCHEDULER_JOB_IDS.values())
    rogue = registered - expected
    assert not rogue, (
        f"Scheduler registers job ids that aren't in SCHEDULER_JOB_IDS: "
        f"{rogue}. Either expose them via personas or remove the job."
    )


def test_list_personas_returns_every_declared_persona():
    """The UI's agents page must show every advertised persona — not a subset."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DB_PATH"] = os.path.join(tmp, "nexus.db")
        from config import settings as _s
        importlib.reload(_s)
        importlib.reload(personas)

        listed = {p["agent_key"] for p in personas.list_personas("biz-test")}
        declared = set(personas.DEFAULTS)

        missing = declared - listed
        assert not missing, (
            f"list_personas omits {missing} — UI won't show them. "
            "Update the `order` list in personas.list_personas to include all "
            "agent keys from DEFAULTS."
        )

        extra = listed - declared
        assert not extra, (
            f"list_personas returns unknown keys {extra} — DEFAULTS doesn't "
            "describe them. Either add to DEFAULTS or remove from order."
        )
