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

Important rules:
- All data you access is scoped to this business only. You cannot see other businesses.
- Some tools require user approval (emails, deletions, sending invoices). \
When that happens, tell the user the action is waiting on the Approvals page.
- Before creating a new contact or company, search first to avoid duplicates.
- For questions about uploaded documents, use search_knowledge. For warehouse \
data questions (sales, revenue), use run_business_query.
- Keep answers concise. When you've completed an action, confirm briefly — \
don't restate the whole plan.
- If the user asks about something preferences-related (billing terms, team \
policies, preferred tools), use `recall` first, then answer.
- When you learn a new durable fact about how this business operates, use \
`remember` to store it so you don't have to re-learn it next session.
- Never fabricate data or results. If a tool failed, say so.
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

    system = _build_system_prompt(business_id, business_name, user_name, last_user_text)
    tools = tool_registry.list_tools(for_llm=True)

    # Compress long conversations before handing them to the LLM — keeps
    # context windows reasonable and costs down.
    compressed = prepare_messages_for_agent(messages)

    # Working copy of the messages (we append as the loop runs)
    working: List[Dict[str, Any]] = [dict(m) for m in compressed]
    tool_calls_record: List[Dict[str, Any]] = []
    pending_approval_ids: List[str] = []

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
        any_error = False
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
                if outcome.get("pending_approval"):
                    pending_approval_ids.append(outcome["approval_id"])
                    result_for_llm = {
                        "status": "queued_for_approval",
                        "approval_id": outcome["approval_id"],
                        "summary": outcome["summary"],
                        "note": "This action is waiting for the user to approve on the Approvals page. Do not retry this exact action.",
                    }
                    tool_calls_record.append({
                        "name": tool_name, "args": args,
                        "pending_approval": True,
                        "approval_id": outcome["approval_id"],
                        "summary": outcome["summary"],
                    })
                else:
                    result_for_llm = outcome.get("result")
                    tool_calls_record.append({
                        "name": tool_name, "args": args,
                        "pending_approval": False,
                        "result_preview": str(result_for_llm)[:300],
                    })
                consecutive_errors = 0
            except Exception as e:
                any_error = True
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

    return {
        "answer": final_text,
        "tool_calls": tool_calls_record,
        "pending_approvals": pending_approval_ids,
        "steps": steps,
        "stop_reason": stop_reason,
    }
