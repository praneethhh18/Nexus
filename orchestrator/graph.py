"""
NexusAgent LangGraph — main orchestration state machine.
Routes queries through RAG, SQL, Action, Report, WhatIf, and Chitchat nodes.
"""
from __future__ import annotations

from typing import Dict, Any

from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("[Graph] LangGraph not available — using fallback pipeline.")

# ── State Schema ──────────────────────────────────────────────────────────────
INITIAL_STATE = {
    "query": "",
    "tone": {},
    "intent": {},
    "rag_results": [],
    "sql_results": {},
    "action_result": {},
    "report_path": "",
    "whatif_result": {},
    "chitchat_answer": "",
    "reflection_passed": False,
    "reflection_attempts": 0,
    "reflection_feedback": "",
    "final_answer": "",
    "citations": [],
    "tools_used": [],
    "warnings": [],
    "error": "",
    "conversation_history": [],
    # ── Tier 1: Multi-Agent Collaboration ─────────────────────────────────
    "multi_agent": False,          # whether multi-agent mode is active
    "agent_plan": None,            # TaskPlan from PlannerAgent
    "agent_results": {},           # Dict[int, AgentResult]
    "agents_used": [],             # List of specialist agent names
    # ── Tier 1: Multi-Document RAG ────────────────────────────────────────
    "multi_doc_result": {},        # Result from multi-doc RAG
    "sources_used": [],            # Document sources used in answer
    "per_source_summaries": {},    # Per-document summaries
    # ── Tier 1: User Memory & Personalization ─────────────────────────────
    "user_id": "default",          # Current user ID
    "personalized_context": "",    # Built from user memory
    "user_profile": {},            # User profile snapshot
}


# ── Routing Logic ─────────────────────────────────────────────────────────────
def _route_intent(state: Dict[str, Any]) -> str:
    """After intent detection, decide which node runs first."""
    tools = state.get("intent", {}).get("tools_needed", [])
    primary = state.get("intent", {}).get("primary_intent", "chitchat")

    # ── Tier 1: Multi-Agent Collaboration ──────────────────────────────
    if state.get("multi_agent"):
        return "multi_agent"

    if primary == "chitchat" and not tools:
        return "chitchat"
    if "rag" in tools and "sql" not in tools:
        return "rag"
    if "sql" in tools and "rag" not in tools and primary != "report_request":
        return "sql"
    if primary == "report_request":
        return "sql"  # get data first, then build report
    if "rag" in tools and "sql" in tools:
        return "rag"  # rag first for hybrid
    if "action" in tools:
        return "action"
    if "whatif" in tools:
        return "whatif"
    return "chitchat"


def _route_after_rag(state: Dict[str, Any]) -> str:
    """After RAG, decide whether to also run SQL or go to synthesizer."""
    tools = state.get("intent", {}).get("tools_needed", [])
    primary = state.get("intent", {}).get("primary_intent", "")

    if "sql" in tools or primary in ("hybrid_query", "report_request"):
        return "sql"
    if "action" in tools:
        return "action"
    return "synthesizer"


def _route_after_sql(state: Dict[str, Any]) -> str:
    """After SQL, decide next step."""
    primary = state.get("intent", {}).get("primary_intent", "")
    tools = state.get("intent", {}).get("tools_needed", [])

    if primary == "report_request" or "report" in tools:
        return "report"
    if "action" in tools:
        return "action"
    return "synthesizer"


def _route_reflection(state: Dict[str, Any]) -> str:
    """After reflection, either retry or finish."""
    if state.get("reflection_passed"):
        return END
    if state.get("reflection_attempts", 0) >= 2:
        return END
    return "synthesizer"


# ── Fallback pipeline (no LangGraph) ─────────────────────────────────────────
def _run_fallback_pipeline(state: Dict[str, Any]) -> Dict[str, Any]:
    """Sequential pipeline when LangGraph is not installed."""
    from orchestrator.nodes import (
        intent_node, rag_node, sql_node, action_node,
        report_node, whatif_node, chitchat_node,
        synthesizer_node,
    )

    state = intent_node(state)

    # ── Tier 1: Multi-Agent Collaboration ──────────────────────────────
    if state.get("multi_agent"):
        from orchestrator.multi_agent import multi_agent_node
        state = multi_agent_node(state)
        state = synthesizer_node(state)
        return state

    tools = state.get("intent", {}).get("tools_needed", [])
    primary = state.get("intent", {}).get("primary_intent", "chitchat")

    if primary == "chitchat" and not tools:
        state = chitchat_node(state)
    else:
        if "rag" in tools:
            state = rag_node(state)
        if "sql" in tools or primary == "report_request":
            state = sql_node(state)
        if "action" in tools:
            state = action_node(state)
        if "report" in tools or primary == "report_request":
            state = report_node(state)
        if "whatif" in tools or primary == "whatif_query":
            state = whatif_node(state)
        if not any(t in tools for t in ["rag", "sql", "action", "report", "whatif"]):
            state = chitchat_node(state)

    state = synthesizer_node(state)
    # Skip reflection — saves 1 LLM call (30-60s) per query
    state["reflection_passed"] = True

    return state


# ── Build graph (if LangGraph available) ─────────────────────────────────────
def _build_graph():
    if not LANGGRAPH_AVAILABLE:
        return None

    from orchestrator.nodes import (
        intent_node, rag_node, sql_node, action_node,
        report_node, whatif_node, chitchat_node,
        synthesizer_node, reflection_node,
    )
    from orchestrator.multi_agent import multi_agent_node

    graph = StateGraph(dict)
    graph.add_node("intent", intent_node)
    graph.add_node("rag", rag_node)
    graph.add_node("sql", sql_node)
    graph.add_node("action", action_node)
    graph.add_node("report", report_node)
    graph.add_node("whatif", whatif_node)
    graph.add_node("chitchat", chitchat_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("reflection", reflection_node)
    # ── Tier 1: Multi-Agent Collaboration ──────────────────────────────
    graph.add_node("multi_agent", multi_agent_node)

    graph.set_entry_point("intent")

    graph.add_conditional_edges("intent", _route_intent, {
        "rag": "rag",
        "sql": "sql",
        "action": "action",
        "report": "sql",
        "whatif": "whatif",
        "chitchat": "chitchat",
        "multi_agent": "multi_agent",
    })

    graph.add_conditional_edges("rag", _route_after_rag, {
        "sql": "sql",
        "action": "action",
        "synthesizer": "synthesizer",
    })

    graph.add_conditional_edges("sql", _route_after_sql, {
        "report": "report",
        "action": "action",
        "synthesizer": "synthesizer",
    })

    for node in ("action", "report", "whatif", "chitchat", "multi_agent"):
        graph.add_edge(node, "synthesizer")

    graph.add_edge("synthesizer", "reflection")

    graph.add_conditional_edges("reflection", _route_reflection, {
        "synthesizer": "synthesizer",
        END: END,
    })

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None and LANGGRAPH_AVAILABLE:
        _compiled_graph = _build_graph()
    return _compiled_graph


def _is_just_chitchat(query: str) -> bool:
    """Check if query is ONLY casual chat (greeting, thanks, etc).
    Everything else goes through the full pipeline.
    Only truly trivial messages skip the pipeline."""
    q = query.lower().strip()

    # Very short greetings
    if len(q) < 15 and any(q.startswith(g) for g in [
        "hi", "hello", "hey", "yo", "sup", "thanks", "thank you",
        "ok", "okay", "cool", "nice", "good", "great", "bye",
        "good morning", "good night", "what's up", "whats up",
    ]):
        return True

    # Questions about capabilities
    if any(k in q for k in ["what can you do", "help me", "who are you", "your name"]):
        return True

    # Everything else → use the full pipeline
    return False


def _fast_chat(query: str, user_id: str = "default") -> Dict[str, Any]:
    """Single LLM call for simple chat. Uses Claude if available, else fast local model."""
    from config.llm_provider import invoke
    from memory.short_term import get_default_memory
    import time

    start = time.time()
    mem = get_default_memory()
    history = mem.get_context_string(max_chars=300)

    history_block = f"\nRecent chat:\n{history}\n" if history else ""

    system = "You are NexusAgent, an AI business assistant. Be concise and helpful. You can query databases, search documents, generate reports, send emails, and run what-if simulations."
    prompt = f"""{history_block}User: {query}"""

    try:
        answer = invoke(prompt, system=system, max_tokens=512).strip()
    except Exception as e:
        answer = f"Connection error: {e}"

    duration_ms = int((time.time() - start) * 1000)

    mem.add_turn("user", query)
    mem.add_turn("assistant", answer, tools_used=[])

    logger.info(f"[FastChat] '{query[:50]}' -> {len(answer)} chars in {duration_ms}ms")

    return {
        **INITIAL_STATE,
        "query": query,
        "final_answer": answer,
        "tools_used": [],
        "citations": [],
        "intent": {"primary_intent": "chitchat", "tools_needed": []},
    }


def run(query: str, tone: Dict[str, Any] = None, user_id: str = "default") -> Dict[str, Any]:
    """
    Main entry point — run a query through the NexusAgent pipeline.

    Uses FAST PATH (1 LLM call) for simple chat.
    Uses FULL PIPELINE (multi-step) only when tools are needed.
    """
    import time

    # ── Fast path: ONLY for greetings/chitchat → 1 LLM call ────────
    if _is_just_chitchat(query):
        return _fast_chat(query, user_id)

    # ── Full pipeline: needs data/docs/actions ────────────────────────
    from memory.short_term import get_default_memory
    from memory.long_term import auto_extract_facts
    from memory.user_memory import (
        get_user_profile, build_personalized_context, start_session,
        learn_from_interaction,
    )
    from orchestrator.multi_agent import get_orchestrator

    start = time.time()

    # Skip tone analysis — use default casual tone to save 1 LLM call
    if tone is None:
        tone = {"tone": "casual", "confidence": 0.8, "suggested_response_style": ""}

    profile = get_user_profile(user_id)
    personalized_context = build_personalized_context(user_id, query)
    session_id = start_session(user_id)

    # Quick multi-agent check (heuristic, no LLM)
    orchestrator = get_orchestrator()
    use_multi_agent = orchestrator.planner.should_use_multi_agent(query)

    state = {
        **INITIAL_STATE,
        "query": query,
        "tone": tone,
        "user_id": user_id,
        "personalized_context": personalized_context,
        "user_profile": profile,
        "multi_agent": use_multi_agent,
    }

    graph = get_graph()
    if graph is not None:
        try:
            final_state = graph.invoke(state)
        except Exception as e:
            logger.error(f"[Graph] LangGraph invoke failed, using fallback: {e}")
            final_state = _run_fallback_pipeline(state)
    else:
        final_state = _run_fallback_pipeline(state)

    duration_ms = int((time.time() - start) * 1000)

    mem = get_default_memory()
    mem.add_turn("user", query)
    mem.add_turn(
        "assistant",
        final_state.get("final_answer", ""),
        tools_used=final_state.get("tools_used", []),
    )

    if mem.turn_count % 10 == 0:
        auto_extract_facts(mem.get_context_string())

    try:
        learn_from_interaction(user_id, query, final_state)
    except Exception as e:
        logger.warning(f"[Graph] User learning failed: {e}")

    try:
        from memory.user_memory import end_session
        end_session(session_id)
    except Exception:
        pass

    logger.info(
        f"[Graph] Query complete in {duration_ms}ms. "
        f"Tools: {final_state.get('tools_used', [])}. "
        f"Multi-agent: {final_state.get('multi_agent', False)}. "
        f"Answer length: {len(final_state.get('final_answer', ''))}"
    )

    return final_state
