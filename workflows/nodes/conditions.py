"""
Condition node implementations.
Conditions return the context with '_branch' set to the chosen output port.
"""
from __future__ import annotations
from typing import Dict, Any
from loguru import logger


def run_value_condition(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    field = config.get("field", "value")
    operator = config.get("operator", "<")
    threshold_raw = config.get("threshold", "0")

    # Extract field from output
    output = ctx.get("output", "")
    data = ctx.get("_last_df_summary", {})

    # Try to get the value
    value = None
    if isinstance(output, dict):
        value = output.get(field)
    elif isinstance(data, dict):
        value = data.get(field)
    elif isinstance(output, (int, float)):
        value = output

    if value is None:
        # Try to parse numeric from string
        try:
            import re
            nums = re.findall(r"[\d.]+", str(output))
            if nums:
                value = float(nums[0])
        except Exception:
            pass

    result = False
    try:
        threshold = float(threshold_raw)
        fval = float(value) if value is not None else 0.0
        ops = {
            "<": fval < threshold, "<=": fval <= threshold,
            ">": fval > threshold, ">=": fval >= threshold,
            "==": fval == threshold, "!=": fval != threshold,
        }
        result = ops.get(operator, False)
    except Exception:
        # String operations
        sval = str(value or output)
        if operator == "contains":
            result = threshold_raw in sval
        elif operator == "not_contains":
            result = threshold_raw not in sval

    ctx["_branch"] = "true" if result else "false"
    ctx["output"] = f"Condition ({field} {operator} {threshold_raw}): {'TRUE' if result else 'FALSE'}"
    logger.debug(f"[Condition] value_condition → branch={ctx['_branch']}")
    return ctx


def run_llm_condition(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    question_template = config.get("question", "Is this critical? Answer YES or NO.\n\n{data}")
    data = str(ctx.get("output", ""))[:2000]
    question = question_template.replace("{data}", data)

    try:
        from config.llm_config import get_llm
        llm = get_llm()
        response = llm.invoke(question).strip().upper()
        answered_yes = "YES" in response or "TRUE" in response
        ctx["_branch"] = "yes" if answered_yes else "no"
        ctx["output"] = f"AI decision: {'YES' if answered_yes else 'NO'}\nReasoning: {response[:200]}"
    except Exception as e:
        ctx["_branch"] = "no"
        ctx["output"] = f"AI condition failed: {e}"

    logger.debug(f"[Condition] llm_condition → branch={ctx['_branch']}")
    return ctx


def run_data_exists_condition(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    min_rows = config.get("min_rows", 1)
    df = ctx.get("_last_df")
    has_data = False

    if df is not None:
        try:
            has_data = len(df) >= min_rows
        except Exception:
            pass
    elif ctx.get("output") and str(ctx.get("output")).strip() not in ("", "None", "[]"):
        has_data = True

    ctx["_branch"] = "has_data" if has_data else "empty"
    ctx["output"] = f"Data check: {'has data' if has_data else 'empty / no data'}"
    return ctx
