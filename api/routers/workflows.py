"""
Workflow CRUD + execution + scheduler. Workflows are user-defined node
graphs — list/create/update/delete, toggle on the scheduler, run on
demand or as a preview without saving.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["workflows"])


@router.get("/api/workflows")
def list_workflows_api(ctx: dict = Depends(get_current_context)):
    from workflows.storage import list_workflows as lw
    return lw(business_id=ctx["business_id"])


@router.get("/api/workflows/node-types")
def get_node_types(ctx: dict = Depends(get_current_context)):
    from workflows.node_registry import NODE_TYPES
    return NODE_TYPES


@router.get("/api/workflows/templates")
def get_workflow_templates(ctx: dict = Depends(get_current_context)):
    from workflows.templates import get_all_templates
    return get_all_templates()


@router.post("/api/workflows/generate-from-text")
def generate_workflow_from_text(body: dict, ctx: dict = Depends(get_current_context)):
    """Take a natural-language description and return a workflow draft (not saved)."""
    description = (body.get("description") or "").strip()
    if not description:
        raise HTTPException(400, "description is required")
    if len(description) > 2000:
        raise HTTPException(400, "description too long (max 2000 chars)")
    from agents.workflow_builder import build_workflow
    try:
        wf = build_workflow(description)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return wf


@router.get("/api/workflows/{wf_id}")
def get_workflow(wf_id: str, ctx: dict = Depends(get_current_context)):
    from workflows.storage import load_workflow
    wf = load_workflow(wf_id, business_id=ctx["business_id"])
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return wf


@router.post("/api/workflows")
def save_workflow_api(wf: dict, ctx: dict = Depends(get_current_context)):
    from workflows.storage import save_workflow as sw, load_workflow
    # If updating, verify ownership
    if wf.get("id"):
        existing = load_workflow(wf["id"], business_id=ctx["business_id"])
        if not existing:
            raise HTTPException(404, "Workflow not found for this business")
    wf_id = sw(wf, business_id=ctx["business_id"], user_id=ctx["user"]["id"])
    return {"id": wf_id}


@router.delete("/api/workflows/{wf_id}")
def delete_workflow_api(wf_id: str, ctx: dict = Depends(get_current_context)):
    from workflows.storage import delete_workflow
    ok = delete_workflow(wf_id, business_id=ctx["business_id"])
    if not ok:
        raise HTTPException(404, "Workflow not found")
    return {"ok": True}


@router.post("/api/workflows/{wf_id}/toggle")
def toggle_workflow(wf_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    from workflows.storage import toggle_enabled
    enabled = bool(body.get("enabled", False))
    ok = toggle_enabled(wf_id, enabled, business_id=ctx["business_id"])
    if not ok:
        raise HTTPException(404, "Workflow not found")
    try:
        from workflows.scheduler import sync_all_workflows
        sync_all_workflows()
    except Exception:
        pass
    return {"ok": True, "enabled": enabled}


@router.post("/api/workflows/{wf_id}/run")
def run_workflow(wf_id: str, ctx: dict = Depends(get_current_context)):
    from workflows.storage import load_workflow
    from workflows.executor import execute_workflow
    wf = load_workflow(wf_id, business_id=ctx["business_id"])
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return execute_workflow(wf)


@router.post("/api/workflows/run-preview")
def run_workflow_preview(wf: dict, ctx: dict = Depends(get_current_context)):
    from workflows.executor import execute_workflow
    # Force the workflow to run within the current business
    wf["business_id"] = ctx["business_id"]
    return execute_workflow(wf)


@router.get("/api/workflows/scheduler/jobs")
def get_scheduler_jobs(ctx: dict = Depends(get_current_context)):
    from workflows.scheduler import get_scheduled_jobs
    return get_scheduled_jobs()


@router.get("/api/workflows/scheduler/history")
def get_workflow_history(limit: int = 30, ctx: dict = Depends(get_current_context)):
    from workflows.scheduler import get_run_history
    return get_run_history(limit)
