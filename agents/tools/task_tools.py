"""Task tools — to-dos with priority, status, due date, CRM linkage."""
from __future__ import annotations

from agents.tool_registry import register_tool
from api import tasks as _tasks


def _list_tasks(ctx, args):
    return _tasks.list_tasks(
        ctx["business_id"],
        status=args.get("status"),
        assignee_id=args.get("assignee_id"),
        search=args.get("search"),
        due_window=args.get("due_window"),
        limit=int(args.get("limit", 50)),
    )


register_tool(
    name="list_tasks",
    description=(
        "List tasks for the current business. Filter by status "
        "(open|in_progress|done|cancelled|active) or due_window (overdue|today|this_week)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "assignee_id": {"type": "string"},
            "search": {"type": "string"},
            "due_window": {"type": "string", "enum": ["overdue", "today", "this_week"]},
            "limit": {"type": "integer", "default": 50},
        },
    },
    handler=_list_tasks,
)


def _create_task(ctx, args):
    return _tasks.create_task(ctx["business_id"], ctx["user_id"], args)


register_tool(
    name="create_task",
    description=(
        "Create a new to-do for the current user. Use this for 'remind me to X' or "
        "when logging a follow-up item."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "default": "normal"},
            "status": {"type": "string", "enum": ["open", "in_progress", "done", "cancelled"], "default": "open"},
            "due_date": {"type": "string", "description": "YYYY-MM-DD"},
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "deal_id": {"type": "string"},
            "tags": {"type": "string"},
        },
        "required": ["title"],
    },
    handler=_create_task,
    summary_fn=lambda a: f"Create task: {a.get('title', '')[:80]}"
                         + (f" (due {a.get('due_date')})" if a.get("due_date") else ""),
)


def _update_task(ctx, args):
    tid = args.pop("task_id")
    return _tasks.update_task(ctx["business_id"], tid, args)


register_tool(
    name="update_task",
    description="Update a task's status, priority, due date, title, or linkages.",
    input_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
            "status": {"type": "string", "enum": ["open", "in_progress", "done", "cancelled"]},
            "due_date": {"type": "string"},
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "deal_id": {"type": "string"},
            "tags": {"type": "string"},
        },
        "required": ["task_id"],
    },
    handler=_update_task,
    summary_fn=lambda a: f"Update task {a.get('task_id')}",
)


def _complete_task(ctx, args):
    return _tasks.update_task(ctx["business_id"], args["task_id"], {"status": "done"})


register_tool(
    name="complete_task",
    description="Shortcut to mark a task as done.",
    input_schema={
        "type": "object",
        "properties": {"task_id": {"type": "string"}},
        "required": ["task_id"],
    },
    handler=_complete_task,
    summary_fn=lambda a: f"Complete task {a.get('task_id')}",
)


def _delete_task(ctx, args):
    _tasks.delete_task(ctx["business_id"], args["task_id"])
    return {"ok": True}


register_tool(
    name="delete_task",
    description="Delete a task. Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"task_id": {"type": "string"}},
        "required": ["task_id"],
    },
    handler=_delete_task,
    summary_fn=lambda a: f"DELETE task {a.get('task_id')}",
)


def _task_summary(ctx, args):
    return _tasks.task_summary(ctx["business_id"], user_id=ctx["user_id"] if args.get("mine") else None)


register_tool(
    name="task_summary",
    description=(
        "Get task counts for the current business: overdue, today, next 7 days, "
        "total open, done today. Pass mine=true to scope to the current user."
    ),
    input_schema={
        "type": "object",
        "properties": {"mine": {"type": "boolean", "default": False}},
    },
    handler=_task_summary,
)
