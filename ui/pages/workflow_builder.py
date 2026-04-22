"""
Workflow Automation Builder — n8n-style visual flow editor.
Panels:
  Left  — workflow list + enable/disable + create/delete
  Center— agraph canvas (nodes + edges)
  Right — node config form (schema-driven) + run button
  Tabs  — History | API Keys | Templates
"""
from __future__ import annotations

import json
import uuid
import streamlit as st
from typing import Dict, Any, List, Optional

# ── Helpers ───────────────────────────────────────────────────────────────────
def _wf_store():
    from workflows import storage
    return storage


def _registry():
    from workflows import node_registry
    return node_registry


def _templates():
    from workflows.templates import get_all_templates
    return get_all_templates()


# ── Session-state bootstrap ───────────────────────────────────────────────────
def _init_state():
    defaults = {
        "wf_selected_id": None,        # currently open workflow id
        "wf_nodes": [],                # list of node dicts
        "wf_edges": [],                # list of edge dicts
        "wf_name": "New Workflow",
        "wf_description": "",
        "wf_dirty": False,             # unsaved changes
        "wf_selected_node_id": None,   # node being configured
        "wf_add_node_type": None,      # pending node-add
        "wf_run_result": None,         # last manual run result
        "wf_edge_src": None,           # edge-drawing state (source node)
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Category colour map ───────────────────────────────────────────────────────
CATEGORY_COLORS = {
    "trigger":   "#1565c0",
    "condition": "#6a1b9a",
    "data":      "#2e7d32",
    "ai":        "#e65100",
    "action":    "#b71c1c",
    "control":   "#37474f",
}

CATEGORY_ICONS = {
    "trigger":   "[T]",
    "condition": "[?]",
    "data":      "[D]",
    "ai":        "[AI]",
    "action":    "[A]",
    "control":   "[C]",
}


# ── agraph helpers ────────────────────────────────────────────────────────────
def _build_agraph(nodes: list, edges: list, selected_id: Optional[str]):
    """Convert workflow dicts to streamlit-agraph Node/Edge objects."""
    try:
        from streamlit_agraph import agraph, Node, Edge, Config
    except ImportError:
        return None, None, None

    reg = _registry()
    ag_nodes = []
    ag_edges = []

    for n in nodes:
        ntype = n.get("type", "")
        ndef = reg.get_node_def(ntype) or {}
        cat = ndef.get("category", "control")
        color = CATEGORY_COLORS.get(cat, "#607d8b")
        icon = CATEGORY_ICONS.get(cat, "[N]")
        label = f"{icon} {n.get('name', ntype)}"
        is_selected = (n["id"] == selected_id)
        ag_nodes.append(Node(
            id=n["id"],
            label=label,
            size=20 if not is_selected else 26,
            color=color if not is_selected else "#fdd835",
            font={"color": "#ffffff", "size": 11},
            title=f"{ntype}\n{n.get('name','')}",
            x=n.get("x", 200),
            y=n.get("y", 200),
        ))

    for e in edges:
        ag_edges.append(Edge(
            source=e["source"],
            target=e["target"],
            label=e.get("label", ""),
            color="#90a4ae",
            font={"size": 10, "color": "#546e7a"},
        ))

    cfg = Config(
        width="100%",
        height=500,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#fdd835",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label", "renderLabel": True},
    )
    return ag_nodes, ag_edges, cfg


# ── Node config form (schema-driven) ─────────────────────────────────────────
def _render_node_config(node: dict) -> dict:
    """Render dynamic form fields for a node's config. Returns updated config."""
    reg = _registry()
    ntype = node.get("type", "")
    ndef = reg.get_node_def(ntype) or {}
    schema = ndef.get("config", {})
    config = dict(node.get("config", {}))

    if not schema:
        st.caption("No configurable fields for this node.")
        return config

    for field_name, field_def in schema.items():
        ftype = field_def.get("type", "text")
        label = field_def.get("label", field_name.replace("_", " ").title())
        default = field_def.get("default", "")
        current = config.get(field_name, default)
        help_text = field_def.get("help", "")
        key = f"cfg_{node['id']}_{field_name}"

        if ftype == "text":
            config[field_name] = st.text_input(label, value=str(current), key=key, help=help_text)

        elif ftype == "textarea":
            config[field_name] = st.text_area(label, value=str(current), key=key, help=help_text, height=100)

        elif ftype == "number":
            mn = field_def.get("min", 0)
            mx = field_def.get("max", 9999)
            try:
                val = int(current)
            except (ValueError, TypeError):
                val = int(default) if default != "" else mn
            config[field_name] = st.number_input(label, min_value=mn, max_value=mx,
                                                   value=val, key=key, help=help_text)

        elif ftype == "select":
            options = field_def.get("options", [])
            try:
                idx = options.index(current)
            except ValueError:
                idx = 0
            config[field_name] = st.selectbox(label, options, index=idx, key=key, help=help_text)

        elif ftype == "bool":
            config[field_name] = st.checkbox(label, value=bool(current), key=key, help=help_text)

        elif ftype == "time":
            config[field_name] = st.text_input(label, value=str(current), key=key,
                                                help=help_text or "Format: HH:MM")

    return config


# ── Load workflow into session state ─────────────────────────────────────────
def _load_wf(wf: dict):
    st.session_state["wf_selected_id"] = wf.get("id")
    st.session_state["wf_nodes"] = list(wf.get("nodes", []))
    st.session_state["wf_edges"] = list(wf.get("edges", []))
    st.session_state["wf_name"] = wf.get("name", "Workflow")
    st.session_state["wf_description"] = wf.get("description", "")
    st.session_state["wf_dirty"] = False
    st.session_state["wf_selected_node_id"] = None
    st.session_state["wf_run_result"] = None


def _new_wf():
    st.session_state["wf_selected_id"] = None
    st.session_state["wf_nodes"] = []
    st.session_state["wf_edges"] = []
    st.session_state["wf_name"] = "New Workflow"
    st.session_state["wf_description"] = ""
    st.session_state["wf_dirty"] = False
    st.session_state["wf_selected_node_id"] = None
    st.session_state["wf_run_result"] = None


# ── Save workflow ─────────────────────────────────────────────────────────────
def _save_current():
    store = _wf_store()
    wf = {
        "id": st.session_state["wf_selected_id"] or f"wf-{uuid.uuid4().hex[:8]}",
        "name": st.session_state["wf_name"],
        "description": st.session_state["wf_description"],
        "nodes": st.session_state["wf_nodes"],
        "edges": st.session_state["wf_edges"],
        "enabled": False,
    }
    # Preserve enabled state if updating existing
    if st.session_state["wf_selected_id"]:
        existing = store.load_workflow(st.session_state["wf_selected_id"])
        if existing:
            wf["enabled"] = existing.get("enabled", False)

    saved_id = store.save_workflow(wf)
    st.session_state["wf_selected_id"] = saved_id
    st.session_state["wf_dirty"] = False
    return saved_id


# ── Run workflow ──────────────────────────────────────────────────────────────
def _run_current():
    if not st.session_state["wf_nodes"]:
        st.warning("No nodes — add at least one node first.")
        return

    wf = {
        "id": st.session_state["wf_selected_id"] or "preview",
        "name": st.session_state["wf_name"],
        "nodes": st.session_state["wf_nodes"],
        "edges": st.session_state["wf_edges"],
        "enabled": True,
    }
    with st.spinner("Running workflow..."):
        from workflows.executor import execute_workflow
        result = execute_workflow(wf)
    st.session_state["wf_run_result"] = result


# ══════════════════════════════════════════════════════════════════════════════
# Main page render
# ══════════════════════════════════════════════════════════════════════════════
def render():
    _init_state()
    store = _wf_store()
    reg = _registry()

    st.markdown("## Workflow Automation Builder")
    st.caption("Build n8n-style automation flows. Workflows are disabled by default — enable them when ready.")

    # ── Top toolbar ───────────────────────────────────────────────────────────
    tb1, tb2, tb3, tb4, tb5 = st.columns([2, 1, 1, 1, 1])
    with tb1:
        wf_name_input = st.text_input(
            "Workflow name", value=st.session_state["wf_name"],
            label_visibility="collapsed", placeholder="Workflow name...",
            key="wf_name_input_top"
        )
        if wf_name_input != st.session_state["wf_name"]:
            st.session_state["wf_name"] = wf_name_input
            st.session_state["wf_dirty"] = True

    with tb2:
        if st.button("+ New", use_container_width=True):
            _new_wf()
            st.rerun()

    with tb3:
        save_label = "Save *" if st.session_state["wf_dirty"] else "Save"
        if st.button(save_label, use_container_width=True):
            _save_current()
            st.success("Saved!")
            st.rerun()

    with tb4:
        if st.button("Run Now", use_container_width=True, type="primary"):
            _run_current()
            st.rerun()

    with tb5:
        wf_id = st.session_state["wf_selected_id"]
        if wf_id:
            wf_data = store.load_workflow(wf_id)
            enabled = wf_data.get("enabled", False) if wf_data else False
            toggle_label = "Disable" if enabled else "Enable"
            if st.button(toggle_label, use_container_width=True):
                store.toggle_enabled(wf_id, not enabled)
                from workflows.scheduler import sync_all_workflows
                sync_all_workflows()
                st.rerun()

    st.divider()

    # ── Main layout: Left | Center | Right ───────────────────────────────────
    left_col, center_col, right_col = st.columns([1, 3, 1.4])

    # ── LEFT: Workflow list ───────────────────────────────────────────────────
    with left_col:
        st.markdown("**Workflows**")
        workflows = store.list_workflows()

        if not workflows:
            st.caption("No workflows yet. Click '+ New' or use a template.")
        else:
            for wf in workflows:
                is_active = (wf["id"] == st.session_state["wf_selected_id"])
                enabled_badge = ":green[ON]" if wf.get("enabled") else ":gray[OFF]"
                btn_style = "primary" if is_active else "secondary"
                wf_label = f"{wf['name']} {enabled_badge}"
                if st.button(wf_label, key=f"wf_btn_{wf['id']}",
                             use_container_width=True, type=btn_style):
                    _load_wf(store.load_workflow(wf["id"]))
                    st.rerun()

        st.markdown("---")
        st.markdown("**Add Node**")

        # Group node types by category
        all_categories = ["trigger", "condition", "data", "ai", "action", "control"]
        for cat in all_categories:
            cat_nodes = {k: v for k, v in reg.NODE_TYPES.items() if v.get("category") == cat}
            if not cat_nodes:
                continue
            icon = CATEGORY_ICONS.get(cat, "[N]")
            color = CATEGORY_COLORS.get(cat, "#607d8b")
            with st.expander(f"{icon} {cat.title()}", expanded=False):
                for ntype, ndef in cat_nodes.items():
                    if st.button(ndef.get("label", ntype), key=f"add_{ntype}",
                                 use_container_width=True):
                        new_node = {
                            "id": f"node-{uuid.uuid4().hex[:6]}",
                            "type": ntype,
                            "name": ndef.get("label", ntype),
                            "config": {
                                k: v.get("default", "")
                                for k, v in ndef.get("config", {}).items()
                            },
                            "x": 200 + len(st.session_state["wf_nodes"]) * 250,
                            "y": 200,
                        }
                        st.session_state["wf_nodes"].append(new_node)
                        st.session_state["wf_selected_node_id"] = new_node["id"]
                        st.session_state["wf_dirty"] = True
                        st.rerun()

    # ── CENTER: Canvas ────────────────────────────────────────────────────────
    with center_col:
        nodes = st.session_state["wf_nodes"]
        edges = st.session_state["wf_edges"]
        selected_nid = st.session_state["wf_selected_node_id"]

        if not nodes:
            st.info("Your canvas is empty. Add nodes from the left panel or load a template below.")
        else:
            # Try agraph first
            try:
                from streamlit_agraph import agraph, Node, Edge, Config
                ag_nodes, ag_edges, cfg = _build_agraph(nodes, edges, selected_nid)
                if ag_nodes is not None:
                    clicked = agraph(nodes=ag_nodes, edges=ag_edges, config=cfg)
                    if clicked and clicked != selected_nid:
                        st.session_state["wf_selected_node_id"] = clicked
                        st.rerun()
            except Exception:
                # Fallback: simple text list
                st.caption("(Visual canvas unavailable — agraph not loaded)")
                for n in nodes:
                    icon = CATEGORY_ICONS.get(
                        _registry().get_node_def(n["type"], {}).get("category", ""), "[N]")
                    is_sel = n["id"] == selected_nid
                    label = f"**{icon} {n['name']}**" if is_sel else f"{icon} {n['name']}"
                    if st.button(label, key=f"canvas_btn_{n['id']}", use_container_width=True):
                        st.session_state["wf_selected_node_id"] = n["id"]
                        st.rerun()

        # ── Edge editor ───────────────────────────────────────────────────────
        if len(nodes) >= 2:
            with st.expander("Connect Nodes (Add / Remove Edges)", expanded=False):
                node_options = {n["id"]: n["name"] for n in nodes}
                src = st.selectbox("From", list(node_options.keys()),
                                   format_func=lambda x: node_options[x],
                                   key="edge_src_sel")
                tgt = st.selectbox("To", list(node_options.keys()),
                                   format_func=lambda x: node_options[x],
                                   key="edge_tgt_sel")

                # Show output labels for the source node
                src_ndef = reg.get_node_def(
                    next((n["type"] for n in nodes if n["id"] == src), ""), {})
                out_labels = src_ndef.get("outputs", [])
                edge_label = ""
                if out_labels:
                    edge_label = st.selectbox("Edge label (branch)", [""] + out_labels,
                                              key="edge_label_sel")
                else:
                    edge_label = st.text_input("Edge label (optional)", key="edge_label_txt")

                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("Add Edge", use_container_width=True):
                        if src != tgt:
                            new_edge = {"source": src, "target": tgt, "label": edge_label}
                            # avoid duplicates
                            existing = [(e["source"], e["target"], e.get("label", ""))
                                        for e in edges]
                            if (src, tgt, edge_label) not in existing:
                                st.session_state["wf_edges"].append(new_edge)
                                st.session_state["wf_dirty"] = True
                                st.rerun()
                with ec2:
                    if edges and st.button("Remove Last Edge", use_container_width=True):
                        st.session_state["wf_edges"].pop()
                        st.session_state["wf_dirty"] = True
                        st.rerun()

                # Edge list
                if edges:
                    for i, e in enumerate(edges):
                        lbl = f"  [{e.get('label','')}]" if e.get("label") else ""
                        src_name = node_options.get(e["source"], e["source"])
                        tgt_name = node_options.get(e["target"], e["target"])
                        ec, ed = st.columns([4, 1])
                        ec.caption(f"{src_name} → {tgt_name}{lbl}")
                        if ed.button("x", key=f"del_edge_{i}"):
                            st.session_state["wf_edges"].pop(i)
                            st.session_state["wf_dirty"] = True
                            st.rerun()

    # ── RIGHT: Node config ────────────────────────────────────────────────────
    with right_col:
        selected_nid = st.session_state["wf_selected_node_id"]
        selected_node = next(
            (n for n in st.session_state["wf_nodes"] if n["id"] == selected_nid), None)

        if selected_node is None:
            st.markdown("**Node Inspector**")
            st.caption("Click a node on the canvas to configure it.")
        else:
            ndef = reg.get_node_def(selected_node["type"]) or {}
            cat = ndef.get("category", "control")
            color = CATEGORY_COLORS.get(cat, "#607d8b")
            icon = CATEGORY_ICONS.get(cat, "[N]")

            st.markdown(f"**{icon} Node Config**")
            st.caption(f"Type: `{selected_node['type']}`")

            # Node name
            new_name = st.text_input("Node name", value=selected_node["name"],
                                     key=f"nname_{selected_nid}")
            if new_name != selected_node["name"]:
                selected_node["name"] = new_name
                st.session_state["wf_dirty"] = True

            st.markdown("---")

            # Dynamic config fields
            updated_config = _render_node_config(selected_node)
            if updated_config != selected_node.get("config"):
                selected_node["config"] = updated_config
                st.session_state["wf_dirty"] = True

            # Node outputs info
            outputs = ndef.get("outputs", [])
            if outputs:
                st.caption(f"Branch outputs: {', '.join(outputs)}")

            st.markdown("---")
            if st.button("Delete Node", key=f"del_node_{selected_nid}",
                         use_container_width=True):
                st.session_state["wf_nodes"] = [
                    n for n in st.session_state["wf_nodes"] if n["id"] != selected_nid
                ]
                st.session_state["wf_edges"] = [
                    e for e in st.session_state["wf_edges"]
                    if e["source"] != selected_nid and e["target"] != selected_nid
                ]
                st.session_state["wf_selected_node_id"] = None
                st.session_state["wf_dirty"] = True
                st.rerun()

    # ── Run result ────────────────────────────────────────────────────────────
    result = st.session_state.get("wf_run_result")
    if result:
        st.divider()
        status = result.get("status", "unknown")
        color_map = {"success": "green", "error": "red"}
        c = color_map.get(status, "orange")
        st.markdown(f"**Last Run** — :{c}[{status.upper()}] "
                    f"| {result.get('duration_ms', 0)} ms "
                    f"| run_id: `{result.get('run_id', '')}`")

        steps = result.get("steps", [])
        if steps:
            import pandas as pd
            rows = []
            for s in steps:
                rows.append({
                    "Node": s.get("node_name", ""),
                    "Type": s.get("node_type", ""),
                    "Status": s.get("status", ""),
                    "ms": s.get("duration_ms", 0),
                    "Output": str(s.get("output", ""))[:120],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=200)

        final = result.get("final_output", "")
        if final:
            with st.expander("Final output"):
                st.text(final[:2000])

    # ══════════════════════════════════════════════════════════════════════════
    # Bottom tabs: History | Templates | API Keys | Scheduler
    # ══════════════════════════════════════════════════════════════════════════
    st.divider()
    tab_hist, tab_tmpl, tab_keys, tab_sched = st.tabs(
        ["Run History", "Templates", "API Keys", "Scheduler"])

    # ── Run History tab ───────────────────────────────────────────────────────
    with tab_hist:
        from workflows.scheduler import get_run_history
        history = get_run_history(30)
        if not history:
            st.caption("No scheduled runs yet.")
        else:
            import pandas as pd
            rows = []
            for h in history:
                rows.append({
                    "Workflow": h.get("workflow_name", ""),
                    "Run ID": h.get("run_id", ""),
                    "Status": h.get("status", ""),
                    "Finished": h.get("finished_at", ""),
                    "ms": h.get("duration_ms", 0),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # ── Templates tab ─────────────────────────────────────────────────────────
    with tab_tmpl:
        st.markdown("Load a pre-built workflow template:")
        templates = _templates()
        for tmpl in templates:
            with st.expander(f"**{tmpl['name']}** — {tmpl.get('description', '')}"):
                tags = tmpl.get("tags", [])
                if tags:
                    st.caption("Tags: " + ", ".join(tags))
                st.caption(f"Nodes: {len(tmpl['nodes'])} | Edges: {len(tmpl['edges'])}")
                if st.button(f"Load '{tmpl['name']}'", key=f"load_tmpl_{tmpl['name']}",
                             use_container_width=True):
                    _load_wf(tmpl)
                    st.session_state["wf_dirty"] = True  # needs save
                    st.success(f"Template loaded. Click Save to persist it.")
                    st.rerun()

    # ── API Keys tab ──────────────────────────────────────────────────────────
    with tab_keys:
        st.markdown("Store API keys for use in HTTP Request nodes.")
        st.caption("Keys are stored locally in an encrypted JSON file.")

        existing_keys = store.load_api_keys()
        if existing_keys:
            st.markdown("**Stored keys:**")
            for kname in existing_keys:
                kc1, kc2 = st.columns([3, 1])
                kc1.code(kname)
                if kc2.button("Delete", key=f"del_key_{kname}"):
                    store.delete_api_key(kname)
                    st.rerun()
        else:
            st.caption("No API keys stored yet.")

        st.markdown("**Add / update a key:**")
        new_key_name = st.text_input("Key name (e.g. OPENAI_API_KEY)", key="new_key_name")
        new_key_val = st.text_input("Key value", type="password", key="new_key_val")
        if st.button("Save Key", use_container_width=True):
            if new_key_name and new_key_val:
                store.save_api_key(new_key_name, new_key_val)
                st.success(f"Key '{new_key_name}' saved.")
                st.rerun()
            else:
                st.warning("Both name and value are required.")

    # ── Scheduler status tab ──────────────────────────────────────────────────
    with tab_sched:
        from workflows.scheduler import get_scheduled_jobs, sync_all_workflows
        sc1, sc2 = st.columns([3, 1])
        sc1.markdown("**Scheduled Jobs**")
        if sc2.button("Sync Now", use_container_width=True):
            sync_all_workflows()
            st.success("Scheduler synced.")
            st.rerun()

        jobs = get_scheduled_jobs()
        if not jobs:
            st.caption("No active scheduled jobs. Enable a workflow with a schedule trigger.")
        else:
            import pandas as pd
            st.dataframe(pd.DataFrame(jobs), use_container_width=True)

        # Workflow enable/disable table
        st.markdown("**All Workflows**")
        wfs = store.list_workflows()
        if wfs:
            for wf in wfs:
                wc1, wc2, wc3 = st.columns([3, 1, 1])
                wc1.write(wf["name"])
                status_txt = ":green[Enabled]" if wf.get("enabled") else ":gray[Disabled]"
                wc2.markdown(status_txt)
                toggle_lbl = "Disable" if wf.get("enabled") else "Enable"
                if wc3.button(toggle_lbl, key=f"sched_toggle_{wf['id']}"):
                    store.toggle_enabled(wf["id"], not wf.get("enabled", False))
                    sync_all_workflows()
                    st.rerun()
