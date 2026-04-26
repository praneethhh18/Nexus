"""
Conversation persistence endpoints — list / fetch / rename / delete / create.
Storage lives in `memory.conversation_store`; we just expose the CRUD surface
the chat UI needs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth import get_current_context

router = APIRouter(tags=["conversations"])


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.get("/api/conversations")
def list_conversations_api(limit: int = 20, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import list_conversations as lc
    return lc(business_id=ctx["business_id"], limit=limit)


@router.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import load_messages, assert_conversation_access
    info = assert_conversation_access(conv_id, ctx["business_id"])
    return {"info": info, "messages": load_messages(conv_id)}


@router.patch("/api/conversations/{conv_id}")
def update_conversation(conv_id: str, body: ConversationUpdate,
                        ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import update_title, assert_conversation_access
    assert_conversation_access(conv_id, ctx["business_id"])
    update_title(conv_id, body.title)
    return {"ok": True}


@router.delete("/api/conversations/{conv_id}")
def delete_conversation_api(conv_id: str, ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import delete_conversation as dc, assert_conversation_access
    assert_conversation_access(conv_id, ctx["business_id"])
    dc(conv_id)
    return {"ok": True}


@router.post("/api/conversations")
def create_new_conversation(ctx: dict = Depends(get_current_context)):
    from memory.conversation_store import create_conversation
    conv_id = create_conversation(user_id=ctx["user"]["id"], business_id=ctx["business_id"])
    return {"conversation_id": conv_id}
