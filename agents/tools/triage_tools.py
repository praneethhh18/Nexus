"""Email triage tool — exposes the per-business inbox triage runner
to the agent so users can say "run email triage" (or hit /triage) and
get the same behaviour the 15-minute scheduler does — on demand.

This wires `agents.email_triage.run_for_business` (which the background
scheduler already calls) into the agent's tool registry. No new code
path — same DB writes, same approval-queue drafts, same audit log.
"""
from __future__ import annotations

from loguru import logger

from agents.tool_registry import register_tool


def _triage_inbox(ctx, args):
    """Run the IMAP triage pass synchronously for this business.

    Returns a small summary the agent can quote back: how many messages
    were processed, plus the per-class counts. Heavy details (drafts
    queued, contacts auto-logged) go to the approval queue + audit log,
    which the user sees in the Inbox panel."""
    from agents import email_triage
    biz = ctx["business_id"]
    try:
        result = email_triage.run_for_business(biz)
    except Exception as e:
        logger.warning(f"[TriageTool] run_for_business failed for {biz}: {e}")
        return {"ok": False, "error": str(e), "processed": 0}

    if "skipped" in result:
        # User hasn't connected their inbox, or it's disabled. Surface
        # the reason so the agent can tell them what to do next.
        return {
            "ok": False,
            "skipped": result["skipped"],
            "processed": 0,
            "hint": (
                "Connect a Gmail/IMAP inbox in Settings → Email to enable triage."
                if result["skipped"] == "no_account"
                else "Email triage is currently disabled. Enable it in Settings → Email."
            ),
        }

    if result.get("error"):
        return {"ok": False, "error": result["error"], "processed": 0}

    processed = result.get("processed", 0)
    messages = result.get("messages") or []
    # Count classifications so the agent's reply is concrete.
    from collections import Counter
    classes = Counter((m.get("classification") or "unknown") for m in messages)
    return {
        "ok": True,
        "processed": processed,
        "classes": dict(classes),
        "drafts_queued": sum(1 for m in messages if m.get("draft_queued")),
        "interactions_logged": sum(1 for m in messages if m.get("interaction_logged")),
    }


register_tool(
    name="triage_inbox",
    description=(
        "Run an on-demand email triage pass on the business's connected inbox. "
        "Pulls unread messages, classifies each (lead / invoice / support / internal / noise), "
        "auto-logs CRM interactions for known senders, and queues approval-required "
        "draft replies. Same logic the 15-minute scheduler runs — this just triggers it now. "
        "Use when the user asks to 'triage email', 'check the inbox', or types /triage."
    ),
    input_schema={
        "type": "object",
        "properties": {},
    },
    handler=_triage_inbox,
    summary_fn=lambda a: "Email triage pass (on demand)",
)
