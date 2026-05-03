"""
Outbound caller (Vox) — heartbeat hook.

Vox calls are triggered by the operator from the CRM contact page (POST
/api/voice/prepare-dial) and run inside `nexuscaller-lab`'s LiveKit Agent
worker — NOT scheduled in this process. There's no batch dialer or queue
on this side any more.

But the persona-↔-scheduler contract (tests/test_persona_schedule_contract.py)
requires every advertised persona in `agents.personas.DEFAULTS` to have a
matching `_register("agent-...", ...)` call in `start_agent_scheduler`.
So we expose a tiny daily heartbeat: it just logs that the lab is the
authoritative dialer for this agent. No work is done here; the actual
calling happens in the lab.
"""
from __future__ import annotations

import os

from loguru import logger


TAG = "outbound-caller"


def heartbeat() -> dict:
    """
    Daily heartbeat. Logs that Vox is configured and where the actual
    dialing happens. Returns a small dict so the run_log can capture
    something other than a bare success.
    """
    lab_url = os.getenv("LAB_URL", "")
    has_lab = bool(lab_url)
    logger.info(
        f"[{TAG}] heartbeat · lab_url_configured={has_lab} "
        f"(calls placed via {lab_url or '(LAB_URL not set)'})"
    )
    return {"lab_url_configured": has_lab, "skipped": True}
