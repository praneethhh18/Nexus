"""
Tone Analyzer — classifies the tone of a message using the local LLM.
Guides how the orchestrator should phrase its response.
"""
from __future__ import annotations

import re
from typing import Dict, Any

from loguru import logger

TONES = ["urgent", "confused", "frustrated", "casual", "formal", "curious"]

RESPONSE_STYLES = {
    "urgent": "Brief, direct, no fluff. Answer in 1-3 sentences maximum.",
    "confused": "Detailed, step-by-step, with examples. Use simple language.",
    "frustrated": "Empathetic, calm, solution-focused. Acknowledge the issue first.",
    "casual": "Conversational and friendly. Can use informal language.",
    "formal": "Professional and structured. Use proper grammar and headings.",
    "curious": "Thorough and educational. Provide context and background.",
}


def analyze_tone(text: str) -> Dict[str, Any]:
    """
    Classify the tone of input text using the local LLM.

    Returns:
        {tone, confidence, suggested_response_style}
    """
    if not text or not text.strip():
        return {
            "tone": "casual",
            "confidence": 0.5,
            "suggested_response_style": RESPONSE_STYLES["casual"],
        }

    try:
        from config.llm_config import get_llm
        llm = get_llm()

        prompt = f"""Classify the tone of this message into exactly one category.
Categories: urgent, confused, frustrated, casual, formal, curious

Message: "{text}"

Reply with ONLY this format:
TONE: <tone>
CONFIDENCE: <0.0 to 1.0>"""

        response = llm.invoke(prompt)
        lines = response.strip().split("\n")
        tone = "casual"
        confidence = 0.7

        for line in lines:
            if line.upper().startswith("TONE:"):
                raw = line.split(":", 1)[1].strip().lower()
                if raw in TONES:
                    tone = raw
            elif line.upper().startswith("CONFIDENCE:"):
                try:
                    nums = re.findall(r"[\d.]+", line)
                    if nums:
                        confidence = min(1.0, max(0.0, float(nums[0])))
                except Exception:
                    pass

        style = RESPONSE_STYLES.get(tone, RESPONSE_STYLES["casual"])
        logger.debug(f"[ToneAnalyzer] '{text[:50]}' → tone: {tone} ({confidence:.0%})")

        return {
            "tone": tone,
            "confidence": round(confidence, 2),
            "suggested_response_style": style,
        }

    except Exception as e:
        logger.warning(f"[ToneAnalyzer] LLM call failed, using default: {e}")
        return {
            "tone": "casual",
            "confidence": 0.5,
            "suggested_response_style": RESPONSE_STYLES["casual"],
        }
