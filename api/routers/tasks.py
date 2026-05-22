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
    # Pass actor_id so the activity feed can stamp who made each
    # change ('Praneeth changed status to in_progress').
    return _tasks.update_task(
        ctx["business_id"], task_id, body, actor_id=ctx["user"]["id"]
    )


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


# ── Task thread: merged activity log + comments ────────────────────────────
# The task detail page reads /api/tasks/{id}/thread to render the
# right-hand history pane in chronological order. Comments are POSTed
# to the same id with a separate endpoint so they get the validation
# and notification side effects in api.task_threads.add_comment.
@router.get("/api/tasks/{task_id}/thread")
def get_task_thread_api(task_id: str, ctx: dict = Depends(get_current_context)):
    # Reading the thread requires reading the task first (cheap auth
    # check, raises 404 if the task isn't this tenant's).
    _tasks.get_task(ctx["business_id"], task_id)
    from api import task_threads as _threads
    return _threads.list_thread(ctx["business_id"], task_id)


@router.post("/api/tasks/{task_id}/comments")
def post_task_comment_api(task_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    # Viewers are write-blocked elsewhere; we let them through here
    # for now so a contractor can leave a note, then tighten when we
    # have the role-on-write story sorted across the rest of the app.
    _tasks.get_task(ctx["business_id"], task_id)
    from api import task_threads as _threads
    return _threads.add_comment(
        business_id=ctx["business_id"],
        task_id=task_id,
        author_id=ctx["user"]["id"],
        body=body.get("body", ""),
    )


@router.delete("/api/tasks/{task_id}/comments/{comment_id}")
def delete_task_comment_api(task_id: str, comment_id: str,
                             ctx: dict = Depends(get_current_context)):
    from api import task_threads as _threads
    # Managers/owners can delete anyone's comments; everyone else only
    # their own. We pass actor_id=None to bypass the author check for
    # managers, otherwise the user's own id so the SQL gate enforces.
    is_manager = ctx["business_role"] in ("owner", "admin")
    ok = _threads.delete_comment(
        business_id=ctx["business_id"],
        comment_id=comment_id,
        actor_id=None if is_manager else ctx["user"]["id"],
    )
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(404, "Comment not found or you don't have permission to delete it.")
    return {"ok": True}
