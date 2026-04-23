"""
LangGraph Node Functions — each node processes the state and returns updated state.
"""
from __future__ import annotations

from typing import Dict, Any

from loguru import logger


# ── Type alias ────────────────────────────────────────────────────────────────
State = Dict[str, Any]


def intent_node(state: State) -> State:
    """Detect intent and determine which tools to activate."""
    from orchestrator.intent_detector import detect_intent
    from memory.short_term import get_default_memory

    query = state.get("query", "")
    tone = state.get("tone", {})
    history = get_default_memory().get_context_string(max_chars=1000)

    intent = detect_intent(query, tone, history)
    state["intent"] = intent
    state["tools_used"] = []
    return state


def rag_node(state: State) -> State:
    """Run RAG retrieval for document-based queries."""
    from rag.multi_document_rag import multi_doc_retrieve

    query = state.get("query", "")
    try:
        result = multi_doc_retrieve(query)
        state["multi_doc_result"] = result
        state["sources_used"] = result.get("sources_used", [])
        state["per_source_summaries"] = result.get("per_source_summaries", {})

        # Also populate rag_results for backward compatibility
        # Build flat results list from multi-doc result
        flat_results = []
        citations = result.get("citations", [])
        for rank, c in enumerate(citations[:5], start=1):
            flat_results.append({
                "text": f"See source summaries in per_source_summaries",
                "source": c.get("source", "Unknown"),
                "page": c.get("page", "?"),
                "confidence": c.get("confidence", 0),
                "rank": rank,
            })
        state["rag_results"] = flat_results if flat_results else []

        if result.get("answer"):
            # Store the multi-doc answer for synthesizer
            state["final_answer"] = result["answer"]

        if result.get("warning"):
            state["warnings"] = state.get("warnings", []) + [result["warning"]]
        tools_used = state.get("tools_used", [])
        if "rag" not in tools_used:
            tools_used.append("rag")
        if result.get("is_multi_doc"):
            if "multi_doc_rag" not in tools_used:
                tools_used.append("multi_doc_rag")
        state["tools_used"] = tools_used
        logger.info(
            f"[RAG Node] Multi-doc: {result.get('is_multi_doc', False)}, "
            f"Sources: {len(state['sources_used'])}"
        )
    except Exception as e:
        logger.error(f"[RAG Node] Error: {e}")
        state["rag_results"] = []
        state["error"] = f"RAG error: {e}"
    return state


def sql_node(state: State) -> State:
    """Run SQL agent for data queries. Sets final_answer directly from SQL explanation."""
    from sql_agent.executor import execute_query

    query = state.get("query", "")
    try:
        result = execute_query(query)
        state["sql_results"] = result
        tools_used = state.get("tools_used", [])
        if "sql" not in tools_used:
            tools_used.append("sql")
        state["tools_used"] = tools_used

        # If SQL succeeded, use its explanation directly as the answer
        # This skips the synthesizer LLM call for pure data queries
        if result.get("success") and result.get("explanation"):
            state["final_answer"] = result["explanation"]

        logger.info(f"[SQL Node] Query returned {len(result.get('dataframe', []))} rows")
    except Exception as e:
        logger.error(f"[SQL Node] Error: {e}")
        state["sql_results"] = {"success": False, "error": str(e), "dataframe": None}
    return state


def action_node(state: State) -> State:
    """Handle action requests (email, notifications)."""
    from action_tools.email_tool import compose_and_send

    query = state.get("query", "")
    try:
        result = compose_and_send(
            recipient="[User will specify]",
            subject_hint=query[:80],
            context=query,
            test_mode=True,  # Never auto-send; require explicit approval
        )
        state["action_result"] = result
        tools_used = state.get("tools_used", [])
        if "action" not in tools_used:
            tools_used.append("action")
        state["tools_used"] = tools_used
    except Exception as e:
        logger.error(f"[Action Node] Error: {e}")
        state["action_result"] = {"error": str(e), "approved": False}
    return state


def report_node(state: State) -> State:
    """
    Generate a PDF report from available data.

    Pipeline:
      1. DataFrame comes from local SQL (already private).
      2. `narrative.generate_narrative` aggregates locally, then sends ONLY
         aggregates to the cloud LLM for polished prose. Raw rows never leave.
      3. Chart + full DataFrame are rendered into the PDF locally.
    """
    from report_generator.chart_selector import select_chart_type
    from report_generator.chart_builder import build_chart
    from report_generator.pdf_builder import build_pdf
    from report_generator.narrative import generate_narrative

    query = state.get("query", "")
    sql_results = state.get("sql_results", {})
    df = sql_results.get("dataframe", None)

    try:
        import pandas as pd

        if df is None or (hasattr(df, "empty") and df.empty):
            # Fall back to a simple query for report data
            from sql_agent.executor import execute_query
            res = execute_query("Show total revenue by region for the last 30 days")
            df = res.get("dataframe", pd.DataFrame())

        chart_type, _ = select_chart_type(df, query) if df is not None and not df.empty else ("table", "")
        fig, png_path = build_chart(df, chart_type, query[:60]) if df is not None else (None, None)

        # Aggregate locally, then let the cloud LLM write the narrative from
        # aggregates only. `mode` tells us where the prose came from.
        narrative = generate_narrative(query, df)
        summary = narrative["narrative"]
        agg = narrative["aggregates"]

        insights = [
            f"Based on {agg.get('row_count', 0)} records across {agg.get('column_count', 0)} fields",
            f"Narrative generated via {narrative['mode']} path — raw rows never left the machine",
            f"Report generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ]

        pdf_path = build_pdf(
            title=f"Report: {query[:60]}",
            executive_summary=summary,
            dataframe=df,
            chart_image_path=png_path,
            key_insights=insights,
        )
        state["report_path"] = pdf_path

        from action_tools.discord_tool import send_report_ready
        send_report_ready(pdf_path)

        tools_used = state.get("tools_used", [])
        if "report" not in tools_used:
            tools_used.append("report")
        state["tools_used"] = tools_used
        logger.info(f"[Report Node] PDF: {pdf_path}")

    except Exception as e:
        logger.error(f"[Report Node] Error: {e}")
        state["report_path"] = ""
        state["error"] = f"Report error: {e}"
    return state


def whatif_node(state: State) -> State:
    """Run what-if scenario simulation."""
    from utils.whatif_simulator import run_full_simulation

    query = state.get("query", "")
    try:
        result = run_full_simulation(query)
        state["whatif_result"] = result
        tools_used = state.get("tools_used", [])
        if "whatif" not in tools_used:
            tools_used.append("whatif")
        state["tools_used"] = tools_used
        logger.info(f"[WhatIf Node] Simulation complete")
    except Exception as e:
        logger.error(f"[WhatIf Node] Error: {e}")
        state["whatif_result"] = {"error": str(e)}
    return state


def chitchat_node(state: State) -> State:
    """Handle general conversation with memory context."""
    from config.llm_provider import invoke as llm_invoke
    from memory.short_term import get_default_memory
    from memory.long_term import build_memory_context

    query = state.get("query", "")
    tone = state.get("tone", {})
    style = tone.get("suggested_response_style", "")
    history = get_default_memory().get_context_string()
    memory_ctx = build_memory_context(query)

    # ── Tier 1: Personalized context ───────────────────────────────────
    personalized_ctx = state.get("personalized_context", "")

    system_intro = (
        "You are NexusAgent, a professional AI business assistant that runs 100% locally. "
        "You can query databases, search documents, generate reports, send emails, and run what-if simulations. "
        "Be friendly, concise, and helpful. If the user asks what you can do, explain your capabilities clearly."
    )

    prompt_parts = [system_intro]
    if personalized_ctx:
        prompt_parts.append(personalized_ctx)
    if memory_ctx:
        prompt_parts.append(f"Long-term context:\n{memory_ctx}")
    if history:
        prompt_parts.append(f"Recent conversation:\n{history}")
    if style:
        prompt_parts.append(f"Response style: {style}")
    prompt_parts.append(f"User: {query}\nNexusAgent:")

    try:
        response = llm_invoke("\n\n".join(prompt_parts), max_tokens=512)
        state["chitchat_answer"] = response.strip()
    except Exception as e:
        logger.error(f"[Chitchat Node] Error: {e}")
        state["chitchat_answer"] = f"Connection error: {e}"
    return state


# ── Tier 1: Multi-Agent Collaboration Node ────────────────────────────────────
def multi_agent_node(state: State) -> State:
    """Execute multi-agent collaboration pipeline."""
    from orchestrator.multi_agent import run_multi_agent

    query = state.get("query", "")
    try:
        result = run_multi_agent(query)

        state["final_answer"] = result.get("answer", "")
        state["agent_plan"] = result.get("plan")
        state["agent_results"] = result.get("agent_results", {})
        state["agents_used"] = result.get("agents_used", [])
        state["multi_agent"] = True

        # Mark tools used
        tools_used = state.get("tools_used", [])
        for agent in state["agents_used"]:
            agent_tool = f"{agent.lower()}_agent"
            if agent_tool not in tools_used:
                tools_used.append(agent_tool)
        state["tools_used"] = tools_used

        logger.info(
            f"[MultiAgent Node] {len(state['agents_used'])} agents used: "
            f"{state['agents_used']}"
        )
    except Exception as e:
        logger.error(f"[MultiAgent Node] Error: {e}")
        state["error"] = f"Multi-agent error: {e}"
        state["multi_agent"] = False

    return state


def synthesizer_node(state: State) -> State:
    """Combine all tool results into a coherent final answer.
    SKIPS LLM call if answer is already set by SQL/RAG/chitchat nodes."""
    from config.llm_provider import invoke as llm_invoke

    # If a tool node already set the answer, skip synthesis LLM call
    existing_answer = state.get("final_answer", "")
    if existing_answer and len(existing_answer) > 20:
        # Just add citations and return — no extra LLM call needed
        sql_results = state.get("sql_results", {})
        rag_results = state.get("rag_results", [])
        citations = [{"source": r.get("source","?"), "page": r.get("page","?"), "confidence": r.get("confidence",0)} for r in rag_results[:5]] if rag_results else []
        state["citations"] = citations
        return state

    query = state.get("query", "")
    rag_results = state.get("rag_results", [])
    sql_results = state.get("sql_results", {})
    action_result = state.get("action_result", {})
    report_path = state.get("report_path", "")
    whatif_result = state.get("whatif_result", {})
    chitchat_answer = state.get("chitchat_answer", "")
    reflection_feedback = state.get("reflection_feedback", "")

    # ── Tier 1: Multi-Agent Results ────────────────────────────────────
    multi_agent = state.get("multi_agent", False)
    agent_results = state.get("agent_results", {})
    agents_used = state.get("agents_used", [])

    # ── Tier 1: Personalized context ───────────────────────────────────
    personalized_ctx = state.get("personalized_context", "")

    parts = []
    citations = []

    # ── Multi-agent answer (skip other synthesis if multi-agent ran) ─────
    if multi_agent and state.get("final_answer"):
        state["citations"] = []
        # Gather citations from agent results
        for step_id, result in agent_results.items():
            if result.metadata.get("citations"):
                citations.extend(result.metadata["citations"])
        state["citations"] = citations
        return state

    # RAG context
    if rag_results:
        rag_context = "\n\n".join(
            f"[Doc {r['rank']}] {r['text'][:400]}" for r in rag_results[:3]
        )
        parts.append(f"DOCUMENT KNOWLEDGE:\n{rag_context}")
        citations = [
            {"source": r["source"], "page": r["page"], "confidence": r["confidence"]}
            for r in rag_results
        ]

    # SQL context
    if sql_results.get("success") and sql_results.get("explanation"):
        parts.append(f"DATA INSIGHT:\n{sql_results['explanation']}")

    # Action context
    if action_result:
        draft = action_result.get("draft", {})
        if draft:
            parts.append(
                f"EMAIL DRAFT PREPARED:\nTo: {draft.get('to','?')}\n"
                f"Subject: {draft.get('subject','?')}\n"
                f"(Awaiting your approval before sending)"
            )

    # Report
    if report_path:
        parts.append(f"PDF REPORT GENERATED: {report_path}")

    # What-if
    if whatif_result and not whatif_result.get("error"):
        parts.append(f"SIMULATION RESULT:\n{whatif_result.get('net_impact', '')}")

    # Chitchat fallback
    if chitchat_answer and not parts:
        state["final_answer"] = chitchat_answer
        state["citations"] = []
        return state

    if not parts and chitchat_answer:
        state["final_answer"] = chitchat_answer
        state["citations"] = citations
        return state

    # Synthesize with LLM
    context_block = "\n\n".join(parts) if parts else "No specific data retrieved."
    tone = state.get("tone", {})
    style = tone.get("suggested_response_style", "")
    missing_hint = f"\nMake sure to include: {reflection_feedback}" if reflection_feedback else ""
    style_hint = f"\nResponse style: {style}" if style else ""
    personal_hint = f"\n{personalized_ctx}" if personalized_ctx else ""

    prompt = f"""You are NexusAgent, a professional AI business assistant that runs locally.{personal_hint}

INSTRUCTIONS:
- Answer the user's question using ONLY the information provided below
- Be specific and use exact numbers from the data when available
- If data comes from documents, mention the source name
- Keep your answer concise but complete (2-5 sentences for simple queries, more for complex ones)
- Format numbers properly (e.g. $1,234,567 not 1234567)
- If the information is insufficient to fully answer, say what you found and what's missing{style_hint}{missing_hint}

USER QUESTION: {query}

AVAILABLE INFORMATION:
{context_block}

Answer:"""

    try:
        answer = llm_invoke(prompt, max_tokens=1024)
        state["final_answer"] = answer.strip()
    except Exception as e:
        logger.error(f"[Synthesizer] LLM failed: {e}")
        state["final_answer"] = context_block[:1000]

    state["citations"] = citations
    state["reflection_feedback"] = ""  # reset after use
    return state


def reflection_node(state: State) -> State:
    """Review the synthesized answer for completeness."""
    from orchestrator.self_reflection import reflect

    query = state.get("query", "")
    answer = state.get("final_answer", "")
    attempts = state.get("reflection_attempts", 0)

    result = reflect(query, answer, attempt=attempts)
    state["reflection_passed"] = result["passed"]
    state["reflection_attempts"] = attempts + 1

    if not result["passed"]:
        state["reflection_feedback"] = result.get("missing", result.get("feedback", ""))

    return state
