"""
Agent loop — orchestrates the LLM + tool-calling + approval flow.

Flow per request:
    1. Build system prompt with business memory and user identity.
    2. Call LLM with the conversation history + tool schemas.
    3. If the model asks to call a tool:
         - Validate and invoke via tool_registry.invoke_tool()
         - If the tool was approval-gated, the response notes that; the
           model is told so and can either summarize or keep planning.
         - Otherwise, the tool runs and the result is appended.
    4. Loop until the model produces a final text answer or we hit MAX_STEPS.

Safety caps:
    - MAX_STEPS = 10 tool iterations per request
    - Per-tool errors are reported back to the model, but a third consecutive
      failure ends the loop with an error message
    - Tool args are always validated against the schema before execution
"""
from __future__ import annotations

import json
import time
from typing import List, Dict, Any, Optional

from loguru import logger

from agents import tool_registry, business_memory
from agents.summarizer import prepare_messages_for_agent
from config.llm_tools import invoke_with_tools

MAX_STEPS = 10
MAX_CONSECUTIVE_ERRORS = 3

# Tools whose output is "ground truth" the LLM must quote verbatim — the
# only inputs the grounding validator should compare the final answer
# against. Reading a contact's email from find_contacts and then making
# up a different one IS a bug. Reading a SaaS-pricing essay from
# research_subject and paraphrasing its bullet points is NOT.
#
# Anything not in this set returns content the LLM is supposed to
# transform / summarise, so its strings won't appear verbatim in the
# answer and shouldn't trip the validator.
_CRM_GROUNDING_TOOLS = {
    "find_contacts", "find_companies", "find_deals", "find_tasks",
    "find_invoices", "find_leads",
    "get_contact", "get_company", "get_deal", "get_task", "get_invoice",
    "list_contacts", "list_companies", "list_deals", "list_tasks",
    "list_invoices",
    "create_contact", "create_company", "create_deal", "create_task",
    "create_invoice",
    "update_contact", "update_company", "update_deal", "update_task",
    "update_invoice",
    "send_email", "send_email_from_template",
}


def _build_system_prompt(business_id: str, business_name: str, user_name: str,
                         query_hint: str = "") -> str:
    """Compose the system prompt with business identity + memory context."""
    memory_block = business_memory.build_memory_context(business_id, query=query_hint, max_entries=10)

    base = f"""You are NexusAgent, an autonomous business assistant for {business_name!r}.
The person you are talking to is {user_name}.

You have tools to interact with this business's CRM, tasks, invoices, \
documents, calendar, and knowledge base. Use them proactively — if the user \
asks you to DO something, use the appropriate tool rather than just \
describing what they should do.

HOW TO PLAN A REQUEST
  1. Decide the minimum steps needed.
  2. For multi-step tasks, do the steps in order. Do not ask clarifying \
questions before trying the obvious interpretation; if something is ambiguous, \
make a reasonable default and state your assumption in the final answer.
  3. Prefer one tool call per turn. Only batch multiple calls if they are \
independent and small.
  4. After each tool result, decide whether you have enough info. If yes, \
answer the user. If not, take one more step.
  5. If a tool returns many rows, summarize — don't echo raw dumps.

Output format:
- Reply to the user in plain text or markdown. Do NOT wrap your answer in \
<thinking>, <response>, or any other XML tags. Do not narrate your reasoning \
out loud — just give the answer directly.
- When a tool produces downloadable files, DO NOT embed the raw server file \
paths (e.g. 'C:\\…\\report.pdf') in your answer — the UI renders proper \
download buttons from the tool output. Just confirm the file was generated \
and briefly describe what's in it.

Important rules:
- All data you access is scoped to this business only. You cannot see other businesses.
- Some tools require user approval (emails, deletions, sending invoices). \
When that happens, tell the user the action is waiting in their **Inbox** \
under the "Needs your approval" section — that's where they can review \
and click Approve or Reject. Do NOT call it 'the approvals page' (there \
is no separate page with that name; pending items live in the Inbox).

CRITICAL — DRAFT vs SEND vs SAVE-TEMPLATE
These three actions are SEPARATE and you must not confuse them:
  - `create_email_template` SAVES a reusable template to the library. It \
does NOT send any email to anyone. ONLY use this when the user \
EXPLICITLY says 'save as template' / 'create a template' / 'add this \
to my templates'. NEVER use it for one-off email drafts.
  - `send_email` actually queues an outbound email for the user to \
approve. ONLY this tool (and `send_email_from_template`) creates an \
approval in the Inbox.

When the user asks 'draft a mail to X', 'email Y', 'send a message \
to Z' — follow this ORDER:

  1. If the user gave only a NAME (no '@' in the recipient string), \
you MUST call `find_contacts` FIRST with that name to look up the \
real email address from the CRM. Read the contact's `email` field. \
Do NOT skip this — fabricating an email like 'praneeth.pk@example.com' \
out of the name + a placeholder domain is forbidden.

  1a. READ the find_contacts result. The response is a JSON object \
with a `contacts` array; each contact has an `email` field. When \
contacts[0].email is present, USE IT as the recipient. NEVER ask the \
user 'please provide the email' if the tool already returned it — \
that's the whole point of calling find_contacts. Similarly, if you \
need a contact_id for create_task / create_deal, READ contacts[0].id \
from the same result — don't ask the user for an ID.

  2. If find_contacts returns NO matching contact (total_count == 0) \
and the recipient might be the user themselves, ask once for the \
email address. Do not guess.

  3. Once you have a REAL email address (either from find_contacts or \
typed verbatim by the user), call `send_email` with:
     - to: the real email (never a *@example.com / *@test.com / \
*@yourdomain.com placeholder — send_email will reject those)
     - subject: an actual, specific subject line
     - body: actual greeting + 1-3 sentences of real content + sign-off

NEVER pass placeholder values like '(body)', '(subject)', '...' — the \
tool will reject those and the user gets nothing.

Do not say 'queued for sending' or 'pending approval' unless you \
actually called send_email and it returned a pending_approval result. \
If the user says 'send' / 'yes please' / 'queue it' after you proposed \
a draft, the next tool call is send_email — NOT create_email_template.
- Before creating a new contact or company, search first to avoid duplicates.
- For questions about uploaded documents, use search_knowledge. For warehouse \
data questions (sales, revenue), use run_business_query.
- DOCUMENT REFERENCE RULE: if the user says "this document", "the document", \
"the file", "the pdf", "this contract", "the offer letter", or any deictic \
reference to a document AND there is a recent assistant message in the \
conversation history mentioning a filename was uploaded (look for "uploaded" \
or "📎"), DO NOT ask the user to clarify which file — extract the filename \
from that recent message and immediately call search_knowledge with a broad \
query like "summary key points" or the filename itself. The user is clearly \
referring to the most recent upload. Asking them to specify which file is \
infuriating after they just uploaded one.
- Keep answers concise. When you've completed an action, confirm briefly — \
don't restate the whole plan.
- If the user asks about something preferences-related (billing terms, team \
policies, preferred tools), use `recall` first, then answer.
- When you learn a new durable fact about how this business operates, use \
`remember` to store it so you don't have to re-learn it next session.

OUTPUT FORMAT
- Write your reply as PLAIN natural-language conversation. Never wrap \
your final answer in a JSON envelope (no `{{"action": ..., "answer": ...}}` \
shape, no ```json``` fences). The user sees your reply directly — \
JSON code blocks look broken to them.
- Markdown formatting (bold, lists, tables) is fine and encouraged for \
clarity; just don't quote the whole reply as code.

GROUNDING — ZERO FABRICATION
- NEVER invent names, emails, phone numbers, or other record values. \
Every concrete value in your reply must appear verbatim in a tool result \
from THIS conversation. If you can't see it in tool output, you don't \
know it — say so, don't guess.
- For position queries ("the 5th contact", "first deal", "last invoice"): \
call the relevant find_* tool with a `limit` LARGE ENOUGH to cover the \
position asked (e.g. limit ≥ 5 for "5th"), then read the value at that \
index of the returned list. If `truncated: true` is in the tool result \
AND the position you need is beyond `returned`, call again with a higher \
limit. Do NOT answer until the actual row is in the tool output.
- For count queries ("how many X"): read `total_count` directly from the \
tool result. Do not count the truncated list.
- If a tool failed or returned nothing useful, say "I don't have that \
information" — don't fill the gap with a plausible-sounding placeholder \
like 'John Doe'.
"""
    if memory_block:
        base += f"\n\n{memory_block}\n"
    return base


def run_agent(
    messages: List[Dict[str, Any]],
    business_id: str,
    business_name: str,
    user_id: str,
    user_name: str,
    user_role: str = "member",
    max_steps: int = MAX_STEPS,
    tool_whitelist: Optional[List[str]] = None,
    system_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the full agent loop.

    messages: conversation history. The last entry should be the user's
              current prompt. Format:
                [{"role": "user", "content": "..."},
                 {"role": "assistant", "content": "..."}, ...]

    Returns:
        {
          "answer": str,                  # final assistant text
          "tool_calls": list,             # record of tools invoked [{name, args, result, pending_approval}]
          "pending_approvals": list,      # approval ids created this turn
          "steps": int,                   # how many loop iterations
          "stop_reason": str,
        }
    """
    # Pull out the latest user text for memory keyword filtering
    last_user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, str):
                last_user_text = c
            elif isinstance(c, list):
                last_user_text = " ".join(b.get("text", "") for b in c if b.get("type") == "text")
            break

    system = system_override or _build_system_prompt(business_id, business_name, user_name, last_user_text)
    tools = tool_registry.list_tools(for_llm=True)
    if tool_whitelist:
        allowed = set(tool_whitelist)
        tools = [t for t in tools if t["name"] in allowed]

    # Tag every cloud LLM call inside this turn with the active business so
    # the cloud_budget tracker can enforce per-business daily caps and record
    # spend against the right tenant.
    from config import cloud_budget as _cb
    _budget_token = _cb.set_active_business(business_id)

    # Compress long conversations before handing them to the LLM — keeps
    # context windows reasonable and costs down.
    compressed = prepare_messages_for_agent(messages)

    # Working copy of the messages (we append as the loop runs)
    working: List[Dict[str, Any]] = [dict(m) for m in compressed]
    tool_calls_record: List[Dict[str, Any]] = []
    pending_approval_ids: List[str] = []
    # Raw tool outputs from this turn — fed to the grounding validator
    # at the end so we can catch fabricated names/emails/phones in the
    # final answer. We keep the full result, not the truncated preview,
    # because the LLM may quote rows we didn't show in the trace UI.
    grounding_evidence: List[Any] = []

    # Seed evidence with the user's OWN message text. If the user wrote
    # "invite Praneeth P K to the party on 26th May", the agent quoting
    # "Praneeth P K", "Party", or "26th May" in the reply is grounded —
    # those words came from the user, not the model's imagination. Before
    # this seed, the bulk-hallucination guard nuked legitimate drafts
    # because the agent quoted nouns from the prompt that don't appear
    # in any CRM tool output.
    try:
        for _m in messages[-3:]:  # last few turns is enough
            if _m.get("role") != "user":
                continue
            _c = _m.get("content", "")
            if isinstance(_c, str) and _c.strip():
                grounding_evidence.append({"_user_prompt": _c})
            elif isinstance(_c, list):
                for _b in _c:
                    if isinstance(_b, dict) and _b.get("type") == "text":
                        grounding_evidence.append({"_user_prompt": _b.get("text", "")})
    except Exception:
        pass

    steps = 0
    consecutive_errors = 0
    final_text = ""
    stop_reason = "end_turn"

    while steps < max_steps:
        steps += 1
        t0 = time.time()
        try:
            response = invoke_with_tools(
                messages=working,
                tools=tools,
                system=system,
                max_tokens=2048,
                temperature=0.1,
                # Agent mode requires NATIVE tool use (Bedrock/Anthropic
                # structured tool_calls). Without force_cloud, the
                # complexity router classified short queries as "local"
                # and the call fell through to Ollama's ReAct JSON-text
                # fallback — which produces ```json{"action":...}```
                # envelopes the user sees as broken output and which
                # don't actually fire tools.
                force_cloud=True,
            )
        except Exception as e:
            logger.exception("[AgentLoop] LLM invocation failed")
            final_text = f"LLM call failed: {e}"
            stop_reason = "error"
            break

        text_part = response.get("text", "")
        tc_list = response.get("tool_calls", [])
        stop_reason = response.get("stop_reason", "end_turn")

        # Append assistant content block to history so the next LLM turn has context
        assistant_content = response.get("assistant_content") or (
            [{"type": "text", "text": text_part}] if text_part else []
        )
        if tc_list and not any(b.get("type") == "tool_use" for b in assistant_content):
            # Ollama path: synthesise tool_use blocks
            for tc in tc_list:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["arguments"],
                })
        working.append({"role": "assistant", "content": assistant_content or [{"type": "text", "text": text_part}]})

        if not tc_list:
            # Final answer
            final_text = text_part or "(no response)"
            break

        # Execute each tool call and append results
        tool_results_block = []
        for tc in tc_list:
            tool_name = tc["name"]
            args = tc.get("arguments", {}) or {}
            tid = tc["id"]

            logger.info(f"[AgentLoop] Tool #{steps}: {tool_name} args={json.dumps(args, default=str)[:160]}")

            try:
                outcome = tool_registry.invoke_tool(
                    tool_name=tool_name,
                    arguments=args,
                    business_id=business_id,
                    user_id=user_id,
                    user_role=user_role,
                )
                # Surface downloadable files produced by any tool. The chat UI
                # turns these into download buttons; the WhatsApp bridge
                # auto-attaches them to the reply.
                produced_files: List[Dict[str, Any]] = []
                if isinstance(outcome.get("result"), dict):
                    produced_files = outcome["result"].get("files") or []

                if outcome.get("pending_approval"):
                    pending_approval_ids.append(outcome["approval_id"])
                    result_for_llm = {
                        "status": "queued_for_approval",
                        "approval_id": outcome["approval_id"],
                        "summary": outcome["summary"],
                        "note": "This action is waiting for the user to approve in the Inbox under 'Needs your approval'. Do not retry this exact action.",
                    }
                    tool_calls_record.append({
                        "name": tool_name, "args": args,
                        "pending_approval": True,
                        "approval_id": outcome["approval_id"],
                        "summary": outcome["summary"],
                    })
                else:
                    result_for_llm = outcome.get("result")
                    record = {
                        "name": tool_name, "args": args,
                        "pending_approval": False,
                        "result_preview": str(result_for_llm)[:300],
                    }
                    if produced_files:
                        record["files"] = produced_files
                    tool_calls_record.append(record)
                    # Capture the full tool result for the grounding
                    # validator. Only tools that READ ground-truth CRM
                    # data count as evidence — research / knowledge /
                    # web-search tools return generic content the LLM
                    # is supposed to paraphrase, and validating an
                    # answer about 'Content Marketing' against an
                    # essay snippet always produces false positives.
                    #
                    # _CRM_GROUNDING_TOOLS lists every tool that reads
                    # user-owned records. Everything else is treated as
                    # narrative content for which no grounding applies.
                    if result_for_llm is not None and tool_name in _CRM_GROUNDING_TOOLS:
                        grounding_evidence.append(result_for_llm)
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                logger.warning(f"[AgentLoop] Tool {tool_name} failed: {e}")
                result_for_llm = {"error": str(e)[:300]}
                tool_calls_record.append({
                    "name": tool_name, "args": args,
                    "pending_approval": False,
                    "error": str(e)[:300],
                })

            # Compact tool results before feeding back to the LLM. If the tool
            # returned a long list, keep the first N items + a count so the
            # model doesn't see a 200-row dump it can't reason about.
            if isinstance(result_for_llm, list) and len(result_for_llm) > 20:
                total = len(result_for_llm)
                result_for_llm = {
                    "items": result_for_llm[:20],
                    "_note": f"Showing 20 of {total} items. Ask the user to refine if needed.",
                    "total_count": total,
                }
            elif isinstance(result_for_llm, dict):
                for k, v in list(result_for_llm.items()):
                    if isinstance(v, list) and len(v) > 20:
                        result_for_llm[k] = v[:20]
                        result_for_llm[f"{k}_total_count"] = len(v)

            result_str = json.dumps(result_for_llm, default=str)
            if len(result_str) > 6000:
                result_str = result_str[:6000] + "...[truncated]"

            tool_results_block.append({
                "type": "tool_result",
                "tool_use_id": tid,
                "content": result_str,
            })

        working.append({"role": "user", "content": tool_results_block})

        elapsed = int((time.time() - t0) * 1000)
        logger.debug(f"[AgentLoop] Step {steps} done in {elapsed}ms")

        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            final_text = "I'm running into repeated errors with the tools. Stopping before I make things worse."
            stop_reason = "error_cap"
            break

    else:
        # max_steps exhausted
        final_text = final_text or "I reached my step limit without finishing. Could you break this into smaller requests?"
        stop_reason = "max_steps"

    # Always release the budget context, even on early break.
    try:
        _cb.reset_active_business(_budget_token)
    except Exception:
        pass

    # Hard grounding check — ONLY when the user was asking about their
    # own data (i.e., at least one tool was called this turn). General-
    # knowledge questions ('how do I find clients', 'software industry
    # trends', 'best practices for SaaS pricing') legitimately mention
    # names/companies/products that the LLM knows from training. With
    # no CRM tool involved, there's no 'evidence' to validate against
    # — every name in a normal answer would look ungrounded and the
    # bulk guard was killing legitimate replies.
    #
    # Rule: skip validation entirely when grounding_evidence is empty.
    # When tools WERE called, the user is asking about THEIR data, and
    # fabricated names are real bugs we want to catch.
    grounding_warnings: List[Dict[str, str]] = []
    BULK_HALLUCINATION_THRESHOLD = 3
    if grounding_evidence:
        try:
            from agents import grounding as _grounding
            evidence = _grounding.collect_evidence(grounding_evidence)
            suspects = _grounding.find_ungrounded(final_text, evidence)
            if suspects:
                grounding_warnings = [{"kind": k, "value": v} for k, v in suspects]
                logger.warning(
                    f"[Grounding] {len(suspects)} ungrounded value(s) in answer: "
                    f"{[f'{k}={v}' for k, v in suspects[:6]]}"
                )
                if len(suspects) >= BULK_HALLUCINATION_THRESHOLD:
                    # Don't ship 25 fake names with a tiny warning footer the
                    # user will miss. Replace the whole reply.
                    final_text = (
                        "I couldn't retrieve real data for that — the response "
                        "I was about to send had multiple unverified values. "
                        "Open the relevant page (Customers, Tasks, Deals, "
                        "Invoices, Documents) to see the actual records, or "
                        "ask a more specific question like \"how many "
                        "contacts do I have?\" or \"the 5th contact\"."
                    )
                    stop_reason = "grounding_block"
                else:
                    final_text = final_text + _grounding.hedge_message(suspects)
        except Exception as e:
            # Validator failures must never break the chat.
            logger.warning(f"[Grounding] validator crashed (non-fatal): {e}")

    return {
        "answer": final_text,
        "tool_calls": tool_calls_record,
        "pending_approvals": pending_approval_ids,
        "steps": steps,
        "stop_reason": stop_reason,
        "grounding_warnings": grounding_warnings,
    }
