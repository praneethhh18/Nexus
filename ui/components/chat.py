"""
Chat interface component for NexusAgent Streamlit UI.
Renders messages with tool badges, source citations, and multi-agent indicators.
"""
from __future__ import annotations

import streamlit as st


TOOL_COLORS = {
    "rag": "#1e40af",
    "sql": "#166534",
    "action": "#9a3412",
    "report": "#581c87",
    "whatif": "#155e75",
    "multi_doc_rag": "#1e3a5f",
    "dataagent_agent": "#1b5e20",
    "docagent_agent": "#4a148c",
    "synthesis_agent": "#bf360c",
}

TOOL_LABELS = {
    "rag": "RAG",
    "sql": "SQL",
    "action": "ACTION",
    "report": "REPORT",
    "whatif": "WHAT-IF",
    "multi_doc_rag": "MULTI-DOC",
    "dataagent_agent": "DATA AGENT",
    "docagent_agent": "DOC AGENT",
    "synthesis_agent": "SYNTHESIS",
}


def render_tool_badges(tools: list[str]) -> str:
    """Render colored tool badges as HTML."""
    badges = []
    for t in tools:
        color = TOOL_COLORS.get(t, "#475569")
        label = TOOL_LABELS.get(t, t.upper().replace("_AGENT", "").replace("_", " "))
        badges.append(
            f'<span style="display:inline-flex;align-items:center;gap:3px;'
            f'background:{color};color:white;padding:2px 10px;'
            f'border-radius:20px;font-size:10px;font-weight:600;'
            f'margin:2px;letter-spacing:0.5px;">{label}</span>'
        )
    return " ".join(badges)


def render_chat_history(messages: list[dict]) -> None:
    """Render the full chat history with enhanced styling."""
    # Show only last 50 messages to prevent session bloat
    display_messages = messages[-50:]
    if len(messages) > 50:
        st.caption(f"Showing last 50 of {len(messages)} messages")

    for msg in display_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        tools = msg.get("tools_used", [])
        citations = msg.get("citations", [])
        sources_used = msg.get("sources_used", [])
        multi_agent = msg.get("multi_agent", False)
        agents_used = msg.get("agents_used", [])
        timestamp = msg.get("timestamp", "")

        if role == "user":
            with st.chat_message("user", avatar="U"):
                st.markdown(content)
                if timestamp:
                    st.markdown(
                        f'<span class="msg-timestamp">{timestamp}</span>',
                        unsafe_allow_html=True,
                    )
        else:
            with st.chat_message("assistant", avatar="N"):
                st.markdown(content)

                # Tool badges
                if tools:
                    st.markdown(
                        render_tool_badges(tools),
                        unsafe_allow_html=True,
                    )

                # Multi-agent collaboration indicator
                if multi_agent and agents_used:
                    agent_labels = ", ".join(
                        a.replace("Agent", "") for a in agents_used
                    )
                    st.markdown(
                        f'<div class="agent-collab">'
                        f'Multi-Agent: {agent_labels}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # Source tracking
                if sources_used:
                    with st.expander(f"Sources ({len(sources_used)})", expanded=False):
                        for src in sources_used:
                            st.markdown(
                                f'<div class="source-citation">{src}</div>',
                                unsafe_allow_html=True,
                            )
                elif citations:
                    with st.expander(f"Sources ({len(citations)})", expanded=False):
                        for c in citations:
                            conf = c.get("confidence", 0)
                            st.markdown(
                                f'<div class="source-citation">'
                                f'<b>{c.get("source", "?")}</b> - '
                                f'Page {c.get("page", "?")} '
                                f'({conf:.0%} confidence)'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                if timestamp:
                    st.markdown(
                        f'<span class="msg-timestamp">{timestamp}</span>',
                        unsafe_allow_html=True,
                    )
