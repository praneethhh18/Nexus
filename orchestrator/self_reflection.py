"""
Self-Reflection — reviews the synthesized answer for completeness and accuracy.
"""
from __future__ import annotations

from typing import Dict, Any

from loguru import logger

from config.settings import MAX_REFLECTION_RETRIES
from config.llm_config import get_llm


def reflect(query: str, answer: str, attempt: int = 0) -> Dict[str, Any]:
    """
    Ask the local LLM to evaluate whether the answer fully addresses the query.

    Returns:
        {passed, feedback, attempt}
    """
    if attempt >= MAX_REFLECTION_RETRIES:
        logger.warning(f"[Reflection] Max retries ({MAX_REFLECTION_RETRIES}) reached — forcing PASS.")
        return {
            "passed": True,
            "feedback": "Max reflection retries reached — accepting answer.",
            "attempt": attempt,
        }

    if not answer or len(answer.strip()) < 20:
        return {
            "passed": False,
            "feedback": "Answer is too short or empty. Generate a complete response.",
            "attempt": attempt,
        }

    try:
        llm = get_llm()
        prompt = f"""Evaluate whether this answer fully and accurately addresses the question.

QUESTION: {query}

ANSWER:
{answer[:2000]}

Is this answer complete, accurate, and helpful?
Reply with EXACTLY:
VERDICT: PASS or FAIL
REASON: <one sentence>
MISSING: <what is missing, or 'nothing' if PASS>"""

        response = llm.invoke(prompt)
        lines = response.strip().split("\n")

        verdict = "PASS"
        reason = ""
        missing = ""

        for line in lines:
            if line.upper().startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()
            elif line.upper().startswith("MISSING:"):
                missing = line.split(":", 1)[1].strip()

        passed = "FAIL" not in verdict
        feedback = f"{reason} {f'Missing: {missing}' if missing and missing.lower() != 'nothing' else ''}".strip()

        status = "PASS" if passed else "FAIL"
        logger.info(f"[Reflection] Attempt {attempt+1}: {status} — {feedback[:80]}")

        try:
            from memory.audit_logger import log_tool_call
            log_tool_call(
                tool="self_reflection",
                input_summary=f"Q: {query[:80]}",
                output_summary=f"{status}: {feedback[:80]}",
                duration_ms=0,
                approved=True,
                success=passed,
            )
        except Exception:
            pass

        return {
            "passed": passed,
            "feedback": feedback,
            "missing": missing,
            "attempt": attempt,
        }

    except Exception as e:
        logger.error(f"[Reflection] LLM call failed: {e}")
        return {
            "passed": True,  # Don't block on reflection failure
            "feedback": f"Reflection check failed: {e}",
            "attempt": attempt,
        }
