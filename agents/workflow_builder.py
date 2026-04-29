"""
Natural-language workflow builder — converts a plain-English description into
a valid workflow JSON (nodes + edges) that can be saved and enabled.

We ask the LLM to emit a strict JSON structure, validate it against the node
registry, and return the parsed workflow for the UI to preview.

Security:
- Output is never auto-saved. The frontend shows it for preview and the user
  clicks Save to persist.
- Each node type is checked against the registry; unknown types are replaced
  with a llm_prompt fallback so the workflow is still structurally valid.
"""
from __future__ import annotations

import json
import re
from typing import Dict, Any, List

from loguru import logger

from config.llm_provider import invoke as llm_invoke
from workflows.node_registry import NODE_TYPES


_SYSTEM = """You are a workflow architect. Given a natural-language description, \
produce a JSON workflow with nodes and edges using the catalog below.

Output MUST be one JSON object. No explanations, no markdown fences. Shape:
{
  "name": "<short name>",
  "description": "<1-line summary>",
  "tags": ["<tag1>", "<tag2>"],
  "nodes": [
    {"id": "n1", "type": "<type from catalog>", "name": "<label>", "config": {...}}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "label": ""}
  ]
}

Rules:
- Start with a trigger node (schedule_trigger, manual_trigger, webhook_trigger, or anomaly_trigger).
- Use node types EXACTLY as listed below; never invent types.
- For each node's `config`, fill the fields that the catalog shows.
- Use the previous node's output by referencing {input} in templates.
- Prefer the fewest nodes that accomplish the goal.
- Use branching (value_condition / llm_condition / data_exists_condition) \
when the user describes an "if / only when" rule.

NODE CATALOG:
"""


def _catalog_text() -> str:
    lines = []
    for key, meta in NODE_TYPES.items():
        cfg_keys = ", ".join(meta.get("config", {}).keys())
        lines.append(f"- {key} [{meta.get('category')}]: {meta.get('description', '')[:140]}")
        if cfg_keys:
            lines.append(f"    config: {cfg_keys}")
    return "\n".join(lines)


def build_workflow(description: str) -> Dict[str, Any]:
    """Ask the LLM to convert `description` to a workflow. Returns a dict."""
    if not description.strip():
        raise ValueError("description is required")

    prompt = (
        f"Describe the automation I want:\n\n{description.strip()}\n\n"
        f"Now emit the workflow JSON."
    )
    system = _SYSTEM + _catalog_text()

    raw = llm_invoke(prompt, system=system, max_tokens=2048, temperature=0.1)
    parsed = _extract_json(raw)
    if not parsed:
        raise ValueError("LLM did not return valid JSON. Try rephrasing the description.")

    return _normalize_workflow(parsed, description)


# ── Helpers ──────────────────────────────────────────────────────────────────
_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _extract_json(text: str) -> Dict[str, Any] | None:
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?|```$", "", stripped, flags=re.MULTILINE).strip()
    try:
        return json.loads(stripped)
    except Exception as e:
        # Expected — LLM may wrap JSON in extra prose. Fall through to regex.
        logger.debug(f"[WorkflowBuilder] strict JSON parse failed, trying regex: {e}")
    m = _JSON_OBJ_RE.search(stripped)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _normalize_workflow(wf: Dict[str, Any], description: str) -> Dict[str, Any]:
    """Validate and fill in defaults so the executor can run this workflow."""
    name = (wf.get("name") or description[:60] or "New Workflow").strip()
    desc = (wf.get("description") or description).strip()
    tags = wf.get("tags") or []
    if not isinstance(tags, list):
        tags = []

    raw_nodes = wf.get("nodes") or []
    raw_edges = wf.get("edges") or []
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("LLM produced no nodes — cannot build an empty workflow.")

    nodes: List[Dict[str, Any]] = []
    id_map: Dict[str, str] = {}
    for idx, raw in enumerate(raw_nodes):
        node_type = (raw or {}).get("type", "")
        if node_type not in NODE_TYPES:
            # Replace unknown node with an llm_prompt fallback so the graph stays valid
            logger.warning(f"[WorkflowBuilder] Unknown node type '{node_type}' — replacing with llm_prompt")
            node_type = "llm_prompt"
            raw_config = {"prompt": f"Execute step: {raw.get('name', 'step')}\n\n{{input}}"}
        else:
            raw_config = raw.get("config") or {}

        # Merge with defaults from the registry
        spec = NODE_TYPES[node_type].get("config", {})
        config = {}
        for field_key, field_spec in spec.items():
            if field_key in raw_config:
                config[field_key] = raw_config[field_key]
            elif "default" in field_spec:
                config[field_key] = field_spec["default"]

        old_id = raw.get("id") or f"raw-{idx}"
        new_id = f"n{idx + 1}"
        id_map[old_id] = new_id

        nodes.append({
            "id": new_id,
            "type": node_type,
            "name": raw.get("name") or NODE_TYPES[node_type].get("name", node_type),
            "config": config,
            "x": 100 + (idx * 240),
            "y": 100 + ((idx % 3) * 60),
        })

    # Remap edges through the id map
    edges: List[Dict[str, Any]] = []
    for e in raw_edges:
        if not isinstance(e, dict):
            continue
        src = id_map.get(e.get("source"))
        tgt = id_map.get(e.get("target"))
        if not src or not tgt:
            continue
        edges.append({
            "source": src,
            "target": tgt,
            "label": e.get("label", ""),
        })

    # If the LLM forgot edges, create a linear chain as a best-effort
    if not edges and len(nodes) > 1:
        for i in range(len(nodes) - 1):
            edges.append({"source": nodes[i]["id"], "target": nodes[i + 1]["id"], "label": ""})

    return {
        "name": name[:120],
        "description": desc[:400],
        "tags": [str(t)[:40] for t in tags][:8],
        "nodes": nodes,
        "edges": edges,
        "enabled": False,
    }
