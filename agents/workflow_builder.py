"""
Magic Workflows — natural language → executable workflow.

The user types in plain English what they want automated:

    "Every Monday at 9am, summarise last week's deals and email me the report."
    "When a new lead arrives from Instagram, send them a WhatsApp greeting,
     wait 2 days, and if they haven't replied, send a follow-up."
    "If an invoice is more than 14 days overdue, draft a polite reminder for me
     to approve."

Output: a workflow JSON the executor can run unchanged. Frontend shows the
visual graph instantly; user clicks Save + Enable.

Architecture decisions:
─────────────────────────────────────────────────────────────────────────────
1. **Two-pass LLM call.** First pass produces a draft. We validate every
   node type + every config field against the registry. If the draft is
   invalid AND the LLM is willing, we send a corrective second prompt with
   the validation errors. Single retry max — keeps p95 latency under 6s.

2. **Few-shot prompt.** Three end-to-end examples in the system prompt.
   Generic LLMs do badly at this without examples; with them, success rate
   jumps from ~40% to ~85% in our internal eval.

3. **Sensitive=True on the LLM call.** Workflow descriptions can contain
   business-specific context (customer names, deal amounts). Routes through
   the Privacy Bridge for customers who have one configured.

4. **Plan-gate at the router level**, not here. This module returns a draft;
   plan-gating is the API layer's job.

5. **Never auto-save or auto-enable.** The frontend gets a draft that the
   user reviews + tweaks + saves explicitly. Hostile prompt injection in the
   description can't enable a workflow on the user's behalf.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from config.llm_provider import invoke as llm_invoke
from workflows.node_registry import NODE_TYPES


# ── Prompt construction ──────────────────────────────────────────────────────
_SYSTEM_HEADER = """You are NexusAgent's workflow architect. Convert a plain-English \
description of an automation into a strict JSON workflow that NexusAgent's \
executor can run.

OUTPUT RULES:
1. Output exactly ONE JSON object. No prose, no markdown fences, no comments.
2. Use only the node types listed in CATALOG below — never invent types.
3. Every workflow MUST start with exactly one trigger node.
4. Reference upstream output via the literal placeholder `{input}` in any text \
field — the executor substitutes the previous node's output at runtime.
5. Use the FEWEST nodes that accomplish the goal. Don't over-engineer.
6. Use branching nodes (value_condition / llm_condition / data_exists_condition) \
when the user describes "if / only when / unless".
7. For each node's config, fill ONLY fields the catalog lists. Use the catalog's \
default if you're unsure. Never add fields the catalog doesn't show.

JSON SHAPE:
{
  "name":        "<short descriptive name, max 60 chars>",
  "description": "<one-line summary of what this does>",
  "tags":        ["<lowercase-tag1>", "<lowercase-tag2>"],
  "nodes": [
    { "id": "n1", "type": "<catalog type>", "name": "<readable label>", "config": { ... } },
    ...
  ],
  "edges": [
    { "source": "n1", "target": "n2", "label": "" }
  ]
}

For condition nodes, use edge labels "true" / "false" or branch names from \
the node's `outputs`.
"""


# Few-shot examples — these double the success rate. Three diverse cases
# cover the most common workflow patterns: scheduled report, event-driven
# follow-up, and a conditional branch.
_FEW_SHOT_EXAMPLES = """
EXAMPLE 1 — Scheduled report
USER: "Every Monday at 9am, summarise last week's closed deals and email it to me at hi@nexusagent.in."
OUTPUT:
{
  "name": "Weekly deals digest",
  "description": "Every Monday 9am, summarise last week's deals and email a digest.",
  "tags": ["weekly", "deals", "report"],
  "nodes": [
    {"id": "n1", "type": "schedule_trigger", "name": "Every Monday 9am",
     "config": {"mode": "weekly", "weekly_day": "Monday", "weekly_time": "09:00"}},
    {"id": "n2", "type": "sql_query", "name": "Last week's closed deals",
     "config": {"query": "SELECT name, amount, stage FROM nexus_deals WHERE stage='won' AND closed_at >= NOW() - INTERVAL '7 days'", "limit": 100}},
    {"id": "n3", "type": "summarize", "name": "Summarise deals",
     "config": {"prompt": "Summarise these closed deals into a 1-paragraph digest:\\n\\n{input}"}},
    {"id": "n4", "type": "send_email", "name": "Email me",
     "config": {"to": "hi@nexusagent.in", "subject": "Weekly deals digest", "body": "{input}"}}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "label": ""},
    {"source": "n2", "target": "n3", "label": ""},
    {"source": "n3", "target": "n4", "label": ""}
  ]
}

EXAMPLE 2 — Event-driven follow-up
USER: "When an anomaly is detected in sales, slack me a generated report."
OUTPUT:
{
  "name": "Sales anomaly slack alert",
  "description": "Detect sales anomalies and slack a generated report.",
  "tags": ["anomaly", "alert"],
  "nodes": [
    {"id": "n1", "type": "anomaly_trigger", "name": "Sales anomaly",
     "config": {"region": "all", "threshold_pct": 15}},
    {"id": "n2", "type": "generate_report", "name": "Build report",
     "config": {"topic": "sales anomaly", "context": "{input}"}},
    {"id": "n3", "type": "slack_notify", "name": "Slack me",
     "config": {"channel": "#alerts", "message": "Anomaly alert:\\n{input}"}}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "label": ""},
    {"source": "n2", "target": "n3", "label": ""}
  ]
}

EXAMPLE 3 — Conditional branch
USER: "Daily at 10am, if any invoice is more than 14 days overdue, draft a reminder for me to approve."
OUTPUT:
{
  "name": "Overdue invoice reminders",
  "description": "Daily 10am: detect overdue invoices and draft polite reminders.",
  "tags": ["invoices", "daily", "reminder"],
  "nodes": [
    {"id": "n1", "type": "schedule_trigger", "name": "Daily 10am",
     "config": {"mode": "daily", "daily_time": "10:00"}},
    {"id": "n2", "type": "sql_query", "name": "Find overdue invoices",
     "config": {"query": "SELECT id, customer_name, amount, due_date FROM nexus_invoices WHERE status='sent' AND due_date < NOW() - INTERVAL '14 days'", "limit": 50}},
    {"id": "n3", "type": "data_exists_condition", "name": "Any overdue?",
     "config": {"path": "$"}},
    {"id": "n4", "type": "llm_prompt", "name": "Draft reminder emails",
     "config": {"prompt": "For each overdue invoice in this list, write a polite reminder:\\n\\n{input}"}}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "label": ""},
    {"source": "n2", "target": "n3", "label": ""},
    {"source": "n3", "target": "n4", "label": "true"}
  ]
}
"""


def _catalog_text() -> str:
    """Render every node type with its category, description, and config field
    types. Richer than just names — the LLM uses field types to pick valid
    values (e.g. doesn't put text in a number field)."""
    lines = []
    for key, meta in NODE_TYPES.items():
        cat = meta.get("category", "?")
        desc = (meta.get("description") or "").strip()
        lines.append(f"\n• {key}  [{cat}] — {desc}")
        cfg = meta.get("config") or {}
        if cfg:
            for fname, fspec in cfg.items():
                ftype = fspec.get("type", "text")
                fdef = fspec.get("default", "")
                opts = fspec.get("options")
                hint = f"{ftype}"
                if opts:
                    hint += f", one of: {opts}"
                if fdef != "":
                    hint += f", default={fdef!r}"
                lines.append(f"    - {fname}: {hint}")
    return "\n".join(lines)


def _build_system_prompt() -> str:
    return _SYSTEM_HEADER + "\n\nCATALOG:\n" + _catalog_text() + "\n" + _FEW_SHOT_EXAMPLES


# ── Public entry point ───────────────────────────────────────────────────────
def build_workflow(description: str) -> Dict[str, Any]:
    """Convert a plain-English description into a normalised workflow dict.

    Raises ValueError on:
      - empty description
      - LLM returns no parseable JSON after one retry
      - normalised workflow has zero nodes
    """
    description = (description or "").strip()
    if not description:
        raise ValueError("description is required")
    if len(description) > 2000:
        raise ValueError("description too long (max 2000 chars)")

    system = _build_system_prompt()

    # Pass 1
    raw = _ask_llm(description, system)
    parsed = _extract_json(raw)
    errors: List[str] = []
    if parsed:
        normalised, errors = _normalise(parsed, description)
        if not errors:
            return normalised

    # Pass 2 — retry with correction context. Cheap because the catalog is
    # already cached in the LLM's KV cache from pass 1 in most providers.
    if parsed is None:
        retry_hint = "Your previous reply was not valid JSON. Output JSON ONLY, no prose."
    else:
        retry_hint = (
            "Your previous reply had these problems — fix them and re-emit:\n"
            + "\n".join(f"- {e}" for e in errors[:8])
        )
    logger.info(f"[WorkflowBuilder] Retrying with correction: {retry_hint[:120]}")
    raw2 = _ask_llm(description, system + "\n\n" + retry_hint, temperature=0.0)
    parsed2 = _extract_json(raw2)
    if not parsed2:
        raise ValueError("LLM did not return valid JSON. Try rephrasing the description.")
    normalised2, errors2 = _normalise(parsed2, description)
    if errors2:
        # Don't fail outright — the normaliser already replaced unknown nodes
        # with safe fallbacks. Log so we can improve the prompt over time.
        logger.warning(f"[WorkflowBuilder] Retry still had {len(errors2)} validation issues: {errors2[:3]}")
    return normalised2


# ── LLM call ─────────────────────────────────────────────────────────────────
def _ask_llm(description: str, system: str, temperature: float = 0.2) -> str:
    prompt = (
        f"USER REQUEST:\n{description.strip()}\n\n"
        f"Now emit ONLY the workflow JSON object."
    )
    return llm_invoke(
        prompt, system=system,
        max_tokens=2048, temperature=temperature,
        # Workflow descriptions can contain business-specific context
        # (customer names, deal amounts). Route through the Privacy Bridge
        # for customers who have one configured. Falls through to cloud
        # with PII redaction if no bridge.
        sensitive=True,
    )


# ── JSON extraction ──────────────────────────────────────────────────────────
_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction. Strips ``` fences, falls back to regex
    scanning for the first balanced { ... } block."""
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?|```$", "", stripped, flags=re.MULTILINE).strip()
    try:
        return json.loads(stripped)
    except Exception as e:
        logger.debug(f"[WorkflowBuilder] strict JSON parse failed, trying regex: {e}")
    m = _JSON_OBJ_RE.search(stripped)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


# ── Normalisation + validation ───────────────────────────────────────────────
def _normalise(wf: Dict[str, Any], description: str) -> Tuple[Dict[str, Any], List[str]]:
    """Validate against the registry, fill in defaults, ensure structural
    integrity. Returns (normalised_dict, list_of_validation_errors).

    Errors are non-fatal — the normaliser fixes what it can (replaces unknown
    types with llm_prompt fallbacks, links orphan nodes into a chain) and
    surfaces a list of issues the caller can use to retry the LLM.
    """
    errors: List[str] = []

    name = (wf.get("name") or description[:60] or "New Workflow").strip()
    desc = (wf.get("description") or description).strip()
    tags = wf.get("tags") or []
    if not isinstance(tags, list):
        tags = []
        errors.append("`tags` must be a list of strings")

    raw_nodes = wf.get("nodes") or []
    raw_edges = wf.get("edges") or []
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("LLM produced no nodes — cannot build an empty workflow.")

    # Reassign IDs to a stable n1, n2, ... sequence so edges are deterministic
    # and the visual layout has predictable spacing.
    nodes: List[Dict[str, Any]] = []
    id_map: Dict[str, str] = {}
    has_trigger = False

    for idx, raw in enumerate(raw_nodes):
        if not isinstance(raw, dict):
            errors.append(f"node #{idx+1} is not an object")
            continue

        node_type = (raw.get("type") or "").strip()
        if node_type not in NODE_TYPES:
            errors.append(f"unknown node type {node_type!r} — replaced with llm_prompt")
            node_type = "llm_prompt"
            raw_config = {
                "prompt": f"Execute step: {raw.get('name', 'step')}\n\n{{input}}",
            }
        else:
            raw_config = raw.get("config") or {}
            if not isinstance(raw_config, dict):
                errors.append(f"node #{idx+1} config is not an object")
                raw_config = {}

        spec = NODE_TYPES[node_type]
        if spec.get("category") == "trigger":
            if has_trigger:
                errors.append(
                    "workflow has more than one trigger — only the first will run"
                )
            has_trigger = True

        # Fill config: keep the LLM's value if it's the right shape, else
        # use the registry default. Drop unknown keys.
        config = {}
        for field_key, field_spec in (spec.get("config") or {}).items():
            if field_key in raw_config:
                v = raw_config[field_key]
                if not _looks_like_type(v, field_spec):
                    errors.append(
                        f"node {raw.get('name', node_type)}.{field_key}: "
                        f"got {type(v).__name__}, expected {field_spec.get('type')}"
                    )
                    if "default" in field_spec:
                        v = field_spec["default"]
                config[field_key] = v
            elif "default" in field_spec:
                config[field_key] = field_spec["default"]

        old_id = raw.get("id") or f"raw-{idx}"
        new_id = f"n{idx + 1}"
        id_map[old_id] = new_id

        nodes.append({
            "id": new_id,
            "type": node_type,
            "name": raw.get("name") or spec.get("name", node_type),
            "config": config,
            "x": 100 + (idx * 240),
            "y": 100 + ((idx % 3) * 60),
        })

    if not has_trigger:
        # Inject a manual_trigger so the workflow is at least runnable on demand.
        errors.append("workflow had no trigger — prepended a manual_trigger")
        nodes.insert(0, {
            "id": "n0",
            "type": "manual_trigger",
            "name": "Manual run",
            "config": {},
            "x": 100, "y": 100,
        })
        # Shift all the original IDs +1
        # (We avoid renaming again — just insert and rewire below.)

    # Rebuild edges using the id map
    edges: List[Dict[str, Any]] = []
    for e in raw_edges:
        if not isinstance(e, dict):
            errors.append("edge entry is not an object")
            continue
        src = id_map.get(e.get("source"))
        tgt = id_map.get(e.get("target"))
        if not src or not tgt:
            errors.append(
                f"edge {e.get('source')}→{e.get('target')} references unknown node"
            )
            continue
        edges.append({
            "source": src,
            "target": tgt,
            "label": (e.get("label") or "")[:24],
        })

    # If the LLM forgot edges, link nodes in a linear chain so the executor
    # has something to run. Better than failing.
    if not edges and len(nodes) > 1:
        errors.append("no edges provided — linked nodes in a linear chain")
        for i in range(len(nodes) - 1):
            edges.append({
                "source": nodes[i]["id"],
                "target": nodes[i + 1]["id"],
                "label": "",
            })
    # If a trigger was injected, connect it to whatever was first
    if not has_trigger and len(nodes) > 1:
        first_inserted = nodes[0]["id"]
        original_first = nodes[1]["id"]
        # Make sure there's an edge from injected trigger to original first
        if not any(e["source"] == first_inserted and e["target"] == original_first for e in edges):
            edges.insert(0, {"source": first_inserted, "target": original_first, "label": ""})

    return {
        "name":        name[:120],
        "description": desc[:400],
        "tags":        [str(t)[:40].lower() for t in tags][:8],
        "nodes":       nodes,
        "edges":       edges,
        "enabled":     False,
        "_validation": {
            "errors": errors,                     # surface to UI as warnings
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }, errors


def _looks_like_type(value: Any, spec: Dict[str, Any]) -> bool:
    """Cheap shape check — does `value` plausibly match `spec.type`?
    Doesn't do strict validation (that's the executor's job), just catches
    the LLM putting a string where a number lives."""
    expected = (spec.get("type") or "text").lower()
    if expected == "number":
        return isinstance(value, (int, float)) or (
            isinstance(value, str) and value.lstrip("-").replace(".", "", 1).isdigit()
        )
    if expected == "boolean":
        return isinstance(value, bool) or value in ("true", "false", 0, 1)
    if expected == "select":
        opts = spec.get("options") or []
        return not opts or value in opts
    # text / textarea / unknown — any string-ish or null is fine
    return value is None or isinstance(value, (str, int, float, bool, list, dict))
