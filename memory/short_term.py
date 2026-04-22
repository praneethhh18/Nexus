"""
Short-Term Memory — maintains last 10 conversation turns in RAM.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger


class ShortTermMemory:
    """In-memory conversation history for the current session."""

    def __init__(self, max_turns: int = 10):
        self._history: deque = deque(maxlen=max_turns)
        self._turn_count = 0

    def add_turn(
        self,
        role: str,
        content: str,
        tools_used: Optional[List[str]] = None,
    ) -> None:
        """
        Add a conversation turn.
        role: 'user' | 'assistant'
        """
        turn = {
            "turn_id": self._turn_count,
            "role": role,
            "content": content,
            "tools_used": tools_used or [],
            "timestamp": datetime.now().isoformat(),
        }
        self._history.append(turn)
        self._turn_count += 1
        logger.debug(f"[STM] Turn {self._turn_count}: {role} ({len(content)} chars)")

    def get_context_string(self, max_chars: int = 3000) -> str:
        """Format history as a string for LLM prompt injection."""
        if not self._history:
            return ""
        lines = []
        for turn in self._history:
            role_label = "User" if turn["role"] == "user" else "NexusAgent"
            tools = f" [tools: {', '.join(turn['tools_used'])}]" if turn["tools_used"] else ""
            lines.append(f"{role_label}{tools}: {turn['content']}")
        result = "\n".join(lines)
        # Truncate if too long (keep most recent)
        if len(result) > max_chars:
            result = result[-max_chars:]
        return result

    def clear(self) -> None:
        """Clear conversation history."""
        self._history.clear()
        self._turn_count = 0
        logger.info("[STM] History cleared.")

    def get_summary(self) -> str:
        """Ask LLM to summarize the conversation so far."""
        if not self._history:
            return "No conversation history."
        try:
            from config.llm_config import get_llm
            llm = get_llm()
            context = self.get_context_string()
            response = llm.invoke(
                f"Summarize this conversation in 2-3 sentences:\n\n{context}"
            )
            return response.strip()
        except Exception as e:
            logger.warning(f"[STM] Summary failed: {e}")
            return f"Conversation with {len(self._history)} turns."

    def get_last_n(self, n: int = 5) -> List[Dict[str, Any]]:
        """Return last n turns as list of dicts."""
        turns = list(self._history)
        return turns[-n:]

    @property
    def turn_count(self) -> int:
        return self._turn_count

    def __len__(self) -> int:
        return len(self._history)


# Module-level singleton
_default_memory = ShortTermMemory()


def get_default_memory() -> ShortTermMemory:
    return _default_memory
