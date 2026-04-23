"""Document tools — generate proposals, SOWs, contracts, offer letters."""
from __future__ import annotations

from agents.tool_registry import register_tool
from api import documents as _docs


def _list_templates(ctx, args):
    return _docs.list_templates()


register_tool(
    name="list_document_templates",
    description="List available document templates with their variables.",
    input_schema={"type": "object", "properties": {}},
    handler=_list_templates,
)


def _generate_document(ctx, args):
    return _docs.generate_document(
        business_id=ctx["business_id"],
        user_id=ctx["user_id"],
        template_key=args["template_key"],
        title=args["title"],
        variables=args.get("variables", {}) or {},
        fmt=args.get("format", "docx"),
    )


register_tool(
    name="generate_document",
    description=(
        "Generate a business document (proposal, sow, contract, offer_letter) "
        "from a template. `variables` is a dict of field→value matching the "
        "template's input variables. Returns {id, filename, file_path}."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "template_key": {"type": "string", "enum": ["proposal", "sow", "contract", "offer_letter"]},
            "title": {"type": "string"},
            "variables": {"type": "object"},
            "format": {"type": "string", "enum": ["docx", "pdf"], "default": "docx"},
        },
        "required": ["template_key", "title"],
    },
    handler=_generate_document,
    summary_fn=lambda a: f"Generate {a.get('template_key')}: {a.get('title', '')[:60]}",
)


def _list_documents(ctx, args):
    return _docs.list_documents(ctx["business_id"], limit=int(args.get("limit", 30)))


register_tool(
    name="list_documents",
    description="List recently generated documents for this business.",
    input_schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "default": 30}},
    },
    handler=_list_documents,
)


def _delete_document(ctx, args):
    _docs.delete_document(ctx["business_id"], args["document_id"])
    return {"ok": True}


register_tool(
    name="delete_document",
    description="Delete a generated document. Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"document_id": {"type": "string"}},
        "required": ["document_id"],
    },
    handler=_delete_document,
    summary_fn=lambda a: f"DELETE document {a.get('document_id')}",
)
