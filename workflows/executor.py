"""
Workflow Executor — topological sort + sequential execution with full error handling.
Logs every step. Handles branching (conditions), cycles, and node failures.
"""
from __future__ import annotations

import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from workflows.node_registry import get_node_def


# ── Node dispatch table ───────────────────────────────────────────────────────
def _get_runner(node_type: str):
    from workflows.nodes import (
        triggers, conditions, data_nodes, ai_nodes, action_nodes
    )
    RUNNERS = {
        # Triggers
        "schedule_trigger":  triggers.run_schedule_trigger,
        "manual_trigger":    triggers.run_manual_trigger,
        "anomaly_trigger":   triggers.run_anomaly_trigger,
        "webhook_trigger":   triggers.run_webhook_trigger,
        # Conditions
        "value_condition":      conditions.run_value_condition,
        "llm_condition":        conditions.run_llm_condition,
        "data_exists_condition": conditions.run_data_exists_condition,
        # Data
        "sql_query":     data_nodes.run_sql_query,
        "rag_search":    data_nodes.run_rag_search,
        "web_search":    data_nodes.run_web_search,
        "data_transform": data_nodes.run_data_transform,
        # AI
        "llm_prompt":       ai_nodes.run_llm_prompt,
        "summarize":        ai_nodes.run_summarize,
        "generate_report":  ai_nodes.run_generate_report,
        "classify":         ai_nodes.run_classify,
        # Actions
        "send_email":      action_nodes.run_send_email,
        "discord_notify":  action_nodes.run_discord_notify,
        "slack_notify":    action_nodes.run_slack_notify,
        "http_request":    action_nodes.run_http_request,
        "save_file":       action_nodes.run_save_file,
        "desktop_notify":  action_nodes.run_desktop_notify,
        # Control
        "wait_node":  action_nodes.run_wait_node,
        "merge_node": action_nodes.run_merge_node,
    }
    return RUNNERS.get(node_type)


# ── Graph helpers ─────────────────────────────────────────────────────────────
def _build_adjacency(nodes: List[dict], edges: List[dict]) -> Tuple[dict, dict]:
    """Build forward adjacency and reverse (parent) maps."""
    forward: Dict[str, List[Tuple[str, str]]] = {n["id"]: [] for n in nodes}
    reverse: Dict[str, List[str]] = {n["id"]: [] for n in nodes}

    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        label = edge.get("label", "")
        if src in forward:
            forward[src].append((tgt, label))
        if tgt in reverse:
            reverse[tgt].append(src)

    return forward, reverse


def _topological_order(nodes: List[dict], edges: List[dict]) -> List[str]:
    """Kahn's algorithm — detects cycles too."""
    forward, reverse = _build_adjacency(nodes, edges)
    in_degree = {n["id"]: len(reverse[n["id"]]) for n in nodes}
    queue = [n["id"] for n in nodes if in_degree[n["id"]] == 0]
    order = []

    while queue:
        nid = queue.pop(0)
        order.append(nid)
        for (child, _) in forward.get(nid, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(order) != len(nodes):
        # Cycle detected — fall back to insertion order
        logger.warning("[Executor] Cycle detected in workflow — using insertion order")
        return [n["id"] for n in nodes]

    return order


# ── Main executor ─────────────────────────────────────────────────────────────
def execute_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow and return a run report.

    Returns:
        {
          run_id, workflow_id, workflow_name,
          started_at, finished_at, duration_ms,
          status, steps, final_output, error
        }
    """
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    started_at = datetime.now().isoformat()
    t_start = time.time()

    wf_id = workflow.get("id", "unknown")
    wf_name = workflow.get("name", "Unnamed Workflow")
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    logger.info(f"[Executor] Starting '{wf_name}' ({run_id})")

    if not nodes:
        return {
            "run_id": run_id, "workflow_id": wf_id, "workflow_name": wf_name,
            "started_at": started_at, "finished_at": datetime.now().isoformat(),
            "duration_ms": 0, "status": "error",
            "steps": [], "final_output": "", "error": "Workflow has no nodes",
        }

    node_map = {n["id"]: n for n in nodes}
    forward, _ = _build_adjacency(nodes, edges)
    exec_order = _topological_order(nodes, edges)

    # Execution context — flows through all nodes
    business_id = workflow.get("business_id", "default")
    created_by = workflow.get("created_by", "default")
    ctx: Dict[str, Any] = {
        "_workflow_name": wf_name,
        "_workflow_id": wf_id,
        "_run_id": run_id,
        "_business_id": business_id,
        "_user_id": created_by,
        "output": "",
    }
    if "_webhook_payload" in workflow:
        ctx["_webhook_payload"] = workflow["_webhook_payload"]

    steps = []
    final_output = ""
    overall_status = "success"

    # Track which nodes to skip due to branching
    skipped_nodes: set = set()

    for node_id in exec_order:
        if node_id not in node_map:
            continue
        node = node_map[node_id]
        node_type = node.get("type", "")
        node_name = node.get("name", node_type)
        config = node.get("config", {})

        # Skip check (from condition branching or trigger _skip)
        if node_id in skipped_nodes or ctx.get("_skip"):
            steps.append({
                "node_id": node_id,
                "node_name": node_name,
                "node_type": node_type,
                "status": "skipped",
                "output": "Skipped (branch condition)",
                "duration_ms": 0,
            })
            continue

        runner = _get_runner(node_type)
        if runner is None:
            steps.append({
                "node_id": node_id, "node_name": node_name, "node_type": node_type,
                "status": "error", "output": f"Unknown node type: {node_type}", "duration_ms": 0,
            })
            continue

        step_start = time.time()
        step_status = "success"
        step_output = ""
        step_error = None

        try:
            ctx = runner(config, ctx)
            step_output = str(ctx.get("output", ""))[:1000]
            logger.debug(f"[Executor] '{node_name}' → {step_output[:80]}")

            # Handle condition branching
            branch = ctx.pop("_branch", None)
            if branch is not None:
                node_def = get_node_def(node_type)
                all_outputs = node_def.get("outputs", [])
                # Get children edges from this node
                for (child_id, edge_label) in forward.get(node_id, []):
                    # If edge label doesn't match chosen branch, skip child
                    if edge_label and edge_label != branch:
                        skipped_nodes.add(child_id)
                        # Also skip all descendants of skipped child
                        _mark_descendants_skipped(child_id, forward, skipped_nodes)

        except Exception as e:
            step_status = "error"
            step_error = str(e)
            step_output = f"Error: {e}"
            overall_status = "error"
            logger.error(f"[Executor] Node '{node_name}' failed: {e}")

        step_duration = int((time.time() - step_start) * 1000)
        steps.append({
            "node_id": node_id,
            "node_name": node_name,
            "node_type": node_type,
            "status": step_status,
            "output": step_output,
            "duration_ms": step_duration,
            "error": step_error,
        })
        final_output = step_output

    duration_ms = int((time.time() - t_start) * 1000)
    finished_at = datetime.now().isoformat()

    # Update workflow stats
    try:
        from workflows.storage import update_run_stats
        update_run_stats(wf_id, overall_status)
    except Exception:
        pass

    # Audit log
    try:
        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="workflow_executor",
            input_summary=f"Workflow: {wf_name}",
            output_summary=f"{len(steps)} steps, status={overall_status}",
            duration_ms=duration_ms,
            approved=True,
            success=(overall_status == "success"),
            business_id=business_id,
            user_id=created_by,
        )
    except Exception:
        pass

    logger.info(f"[Executor] '{wf_name}' done in {duration_ms}ms — {overall_status}")

    return {
        "run_id": run_id,
        "workflow_id": wf_id,
        "workflow_name": wf_name,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "status": overall_status,
        "steps": steps,
        "final_output": final_output,
        "error": None if overall_status == "success" else "One or more nodes failed",
    }


def _mark_descendants_skipped(node_id: str, forward: dict, skipped: set) -> None:
    """Recursively mark all downstream nodes as skipped."""
    for (child, _) in forward.get(node_id, []):
        if child not in skipped:
            skipped.add(child)
            _mark_descendants_skipped(child, forward, skipped)
