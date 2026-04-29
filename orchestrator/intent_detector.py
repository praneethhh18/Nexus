"""
Intent Detector — classifies user query intent and selects tools needed.
"""
from __future__ import annotations

from typing import Dict, Any

from loguru import logger

from config.llm_provider import invoke as llm_invoke

INTENT_TYPES = [
    "document_query",   # answer from documents/RAG
    "data_query",       # answer from database/SQL
    "hybrid_query",     # needs both RAG + SQL
    "action_request",   # send email / notification
    "report_request",   # generate PDF report
    "whatif_query",     # scenario simulation
    "chitchat",         # general conversation
]

TOOL_MAP = {
    "document_query": ["rag"],
    "data_query": ["sql"],
    "hybrid_query": ["rag", "sql"],
    "action_request": ["action"],
    "report_request": ["sql", "report"],
    "whatif_query": ["whatif"],
    "chitchat": [],
}

URGENCY_KEYWORDS = {"urgent", "asap", "immediately", "critical", "now", "emergency"}


def detect_intent(query: str, tone: Dict[str, Any] = None,
                  history: str = "") -> Dict[str, Any]:
    """
    Classify the intent of a user query.

    Returns:
        {primary_intent, secondary_intents, tools_needed, urgency_level}
    """
    if not query.strip():
        return {
            "primary_intent": "chitchat",
            "secondary_intents": [],
            "tools_needed": [],
            "urgency_level": "low",
        }

    urgency = "high" if any(w in query.lower() for w in URGENCY_KEYWORDS) else "low"
    if tone and tone.get("tone") == "urgent":
        urgency = "high"

    try:
        history_block = f"\nRecent conversation context:\n{history}\n" if history else ""

        prompt = f"""Classify this user request into one intent.

Intents: document_query, data_query, hybrid_query, action_request, report_request, whatif_query, chitchat

Examples:
"Show me revenue by region" -> PRIMARY: data_query
"What does the policy say about PTO?" -> PRIMARY: document_query
"Send a summary email" -> PRIMARY: action_request
"Generate a sales report" -> PRIMARY: report_request
"What if we cut prices by 15%?" -> PRIMARY: whatif_query
"Hello" -> PRIMARY: chitchat
{history_block}
User: "{query}"

Reply ONLY:
PRIMARY: <intent>
SECONDARY: <intent> (or NONE)"""

        response = llm_invoke(prompt, max_tokens=50)
        lines = response.strip().split("\n")

        primary = "chitchat"
        secondary = []

        for line in lines:
            if line.upper().startswith("PRIMARY:"):
                raw = line.split(":", 1)[1].strip().lower().replace("-", "_")
                if raw in INTENT_TYPES:
                    primary = raw
            elif line.upper().startswith("SECONDARY:"):
                raw = line.split(":", 1)[1].strip().lower()
                if raw != "none":
                    for part in raw.split(","):
                        intent = part.strip().replace("-", "_")
                        if intent in INTENT_TYPES and intent != primary:
                            secondary.append(intent)

        tools = list(set(TOOL_MAP.get(primary, [])))
        for sec in secondary:
            tools.extend(TOOL_MAP.get(sec, []))
        tools = list(dict.fromkeys(tools))  # deduplicate, preserve order

        logger.info(
            f"[Intent] '{query[:60]}' → primary={primary}, "
            f"secondary={secondary}, tools={tools}, urgency={urgency}"
        )

        return {
            "primary_intent": primary,
            "secondary_intents": secondary,
            "tools_needed": tools,
            "urgency_level": urgency,
        }

    except Exception as e:
        logger.error(f"[Intent] Detection failed, defaulting to chitchat: {e}")
        return {
            "primary_intent": "chitchat",
            "secondary_intents": [],
            "tools_needed": [],
            "urgency_level": urgency,
        }
