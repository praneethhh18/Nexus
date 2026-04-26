"""Tasks router — list, CRUD, bulk operations."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from api import tasks as _tasks
from api.auth import get_current_context

router = APIRouter(tags=["tasks"])


@router.get("/api/tasks")
def list_tasks_api(
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    search: Optional[str] = None,
    due_window: Optional[str] = None,
    limit: int = 200,
    ctx: dict = Depends(get_current_context),
):
    return _tasks.list_tasks(
        ctx["business_id"], status=status, assignee_id=assignee_id,
        search=search, due_window=due_window, limit=limit,
    )


@router.post("/api/tasks")
def create_task_api(body: dict, ctx: dict = Depends(get_current_context)):
    if body.get("assignee_id") and body["assignee_id"] != ctx["user"]["id"]:
        from api.businesses import assert_member
        assert_member(ctx["business_id"], body["assignee_id"])
    return _tasks.create_task(ctx["business_id"], ctx["user"]["id"], body)


@router.get("/api/tasks/summary")
def task_summary_api(mine: bool = False, ctx: dict = Depends(get_current_context)):
    return _tasks.task_summary(ctx["business_id"], user_id=ctx["user"]["id"] if mine else None)


@router.get("/api/tasks/{task_id}")
def get_task_api(task_id: str, ctx: dict = Depends(get_current_context)):
    return _tasks.get_task(ctx["business_id"], task_id)


@router.patch("/api/tasks/{task_id}")
def update_task_api(task_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    if body.get("assignee_id") and body["assignee_id"] != ctx["user"]["id"]:
        from api.businesses import assert_member
        assert_member(ctx["business_id"], body["assignee_id"])
    return _tasks.update_task(ctx["business_id"], task_id, body)


@router.delete("/api/tasks/{task_id}")
def delete_task_api(task_id: str, ctx: dict = Depends(get_current_context)):
    _tasks.delete_task(ctx["business_id"], task_id)
    return {"ok": True}


@router.post("/api/tasks/bulk-delete")
def bulk_delete_tasks_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    return {"deleted": _tasks.bulk_delete(ctx["business_id"], ids)}


@router.post("/api/tasks/bulk-status")
def bulk_status_tasks_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    status = body.get("status") or ""
    return {"updated": _tasks.bulk_update_status(ctx["business_id"], ids, status)}
