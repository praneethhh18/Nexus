"""
Complexity-based LLM routing — decides "cloud" or "local" for each request.

No extra LLM call is made. Pure heuristic, runs in < 1 ms.

Decision logic:
  local  — Simple CRUD, short lookup, first verb is a known action word, no
            complexity keywords, short prompt.
  cloud  — Drafting, analysis, comparison, research, report generation, long
            prompts, deep conversation history, or multi-tool agent turns
            where reasoning quality matters.

Callers only see `classify()`. The flags `sensitive` and `force_cloud` are
handled upstream in llm_provider/llm_tools; this module is complexity-only.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any

# ── Signal tables ─────────────────────────────────────────────────────────────

_CLOUD_KW = frozenset([
    # Creative / generative
    "draft", "write", "compose", "generate a", "create a report",
    "prepare a", "craft",
    # Analytical
    "analyze", "analyse", "analysis", "evaluate", "assess",
    "compare", "comparison", "contrast", "difference between",
    "pros and cons", "tradeoffs",
    # Explanatory / research
    "explain", "elaborate", "break down", "help me understand",
    "research", "investigate", "deep dive",
    # Summarisation
    "summarize", "summarise", "summary", "tldr",
    # Strategic
    "plan", "strategy", "roadmap", "forecast", "predict",
    "recommendation", "suggest", "propose", "advise",
    # Conditional / hypothetical
    "what if", "how would", "how does", "why does", "why did",
    "based on", "given that", "taking into account", "considering",
    # Document / report
    "report", "document", "presentation", "email to", "letter to",
    "follow-up email", "followup email", "proposal",
    # Multi-step reasoning cues
    "step by step", "detailed", "comprehensive", "in depth",
    "thoroughly", "across all",
    # NexusAgent domain: always-complex operations
    "triage", "briefing", "morning brief", "evening digest",
    "workflow", "automation", "build a workflow",
    "narrative", "digest", "consolidate", "pipeline analysis",
    "meeting prep", "call script", "outreach", "pitch",
])

# First verb = simple action → strongly local
_LOCAL_FIRST_VERBS = frozenset([
    "create", "add", "update", "delete", "remove",
    "list", "get", "find", "search", "show", "fetch",
    "check", "save", "mark", "log", "import",
    "schedule", "book", "cancel", "set", "assign",
    "tag", "filter", "sort",
])

# Short greetings / housekeeping that are always local
_LOCAL_EXACT = frozenset([
    "hi", "hello", "hey", "thanks", "thank you", "ok", "okay",
    "yes", "no", "sure", "got it", "done",
])

# Phrases that spike complexity regardless of length
_CLOUD_PHRASES = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bdraft\s+(a|an|the)\b",
        r"\bwrite\s+(a|an|the)\b",
        r"\banalyze\b",
        r"\bsummar(ize|ise)\b",
        r"\bcompare\b",
        r"\breport\b",
        r"\bstrategy\b",
        r"\bproposal\b",
        r"\bevaluate\b",
        r"\bforecast\b",
        r"\btranslate\b",
        r"\bwhy\s+(are|is|do|did|were|was|have|has|doesn't|don't|didn't)\b",
        r"\bhow\s+(can|could|should|do|does|would|might)\b",
    ]
]

# ── Thresholds ────────────────────────────────────────────────────────────────

_WORD_THRESHOLD_CLOUD = 80     # > 80 words → complex regardless of keywords
_WORD_THRESHOLD_MEDIUM = 40    # 40-80 words → check keywords
_MSG_DEPTH_CLOUD = 8           # > 8 messages in history → complex conversation
_TOOL_COUNT_CLOUD = 4          # > 4 tools → rich agent context, use cloud


# ── Public API ────────────────────────────────────────────────────────────────

def classify(
    prompt: str,
    *,
    system: str = "",
    messages: List[Dict[str, Any]] | None = None,
    tools: List[Dict[str, Any]] | None = None,
) -> str:
    """
    Returns "cloud" or "local".

    prompt   — the current user message or combined prompt string
    system   — the system prompt (also checked for complexity cues)
    messages — full conversation history; depth signals complexity
    tools    — list of tool definitions; many tools → complex agent
    """
    messages = messages or []
    tools = tools or []

    text = prompt.strip()
    lower = text.lower()

    # ── Trivial / exact match: always local ──────────────────────────────────
    if lower in _LOCAL_EXACT:
        return "local"

    # ── Token estimate ───────────────────────────────────────────────────────
    combined = (text + " " + system).strip()
    words = combined.split()
    word_count = len(words)

    if word_count > _WORD_THRESHOLD_CLOUD:
        return "cloud"

    # ── Conversation depth ───────────────────────────────────────────────────
    if len(messages) > _MSG_DEPTH_CLOUD:
        return "cloud"

    # ── Regex phrase check (highest specificity) ─────────────────────────────
    for pat in _CLOUD_PHRASES:
        if pat.search(combined):
            return "cloud"

    # ── Keyword scoring ──────────────────────────────────────────────────────
    cloud_score = 0
    for kw in _CLOUD_KW:
        if kw in lower:
            cloud_score += 1

    # Multiple cloud keywords → definitely complex
    if cloud_score >= 2:
        return "cloud"

    # ── Tool count ───────────────────────────────────────────────────────────
    if len(tools) > _TOOL_COUNT_CLOUD:
        cloud_score += 1

    # ── First-verb CRUD check ────────────────────────────────────────────────
    first_word = words[0].lower().rstrip("s") if words else ""
    is_crud = first_word in _LOCAL_FIRST_VERBS

    # Short CRUD prompt: strong local signal
    if is_crud and word_count <= _WORD_THRESHOLD_MEDIUM:
        # Even one cloud keyword overrides CRUD for medium-length prompts
        if cloud_score == 0:
            return "local"

    # ── Default tie-break ────────────────────────────────────────────────────
    # If cloud scored anything, send to cloud; otherwise stay local.
    if cloud_score >= 1:
        return "cloud"

    return "local"


def explain(
    prompt: str,
    *,
    system: str = "",
    messages: List[Dict[str, Any]] | None = None,
    tools: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Debug helper — returns the routing decision with the signals that drove it.
    Not called in production; useful from the Python REPL.
    """
    messages = messages or []
    tools = tools or []
    combined = (prompt.strip() + " " + system.strip()).strip()
    lower = combined.lower()
    words = combined.split()
    word_count = len(words)
    first_word = words[0].lower().rstrip("s") if words else ""

    matched_cloud_kw = [kw for kw in _CLOUD_KW if kw in lower]
    matched_phrases = [p.pattern for p in _CLOUD_PHRASES if p.search(combined)]
    decision = classify(prompt, system=system, messages=messages, tools=tools)

    return {
        "decision": decision,
        "word_count": word_count,
        "msg_depth": len(messages),
        "tool_count": len(tools),
        "first_word": first_word,
        "is_crud": first_word in _LOCAL_FIRST_VERBS,
        "cloud_keywords": matched_cloud_kw,
        "cloud_phrases": matched_phrases,
    }
