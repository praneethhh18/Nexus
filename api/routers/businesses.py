"""
Business + member management endpoints.

A "business" is the tenant boundary every authed request scopes to. Users can
own multiple businesses and be members of others; members have a role
(owner/admin/member) that gates which mutations they can perform.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth import get_current_user
from api.businesses import (
    create_business, get_business,
    update_business, delete_business,
    list_user_businesses,
    list_members, add_member, remove_member, assert_member,
)

router = APIRouter(tags=["businesses"])


class BusinessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    industry: str = ""
    description: str = ""


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    industry: Optional[str] = None
    description: Optional[str] = None


class MemberAdd(BaseModel):
    user_id: str
    role: str = "member"


@router.get("/api/businesses")
def list_my_businesses(user: dict = Depends(get_current_user)):
    return list_user_businesses(user["id"])


@router.post("/api/businesses")
def create_my_business(req: BusinessCreate, user: dict = Depends(get_current_user)):
    return create_business(
        name=req.name,
        owner_id=user["id"],
        industry=req.industry,
        description=req.description,
    )


@router.get("/api/businesses/{business_id}")
def get_my_business(business_id: str, user: dict = Depends(get_current_user)):
    assert_member(business_id, user["id"])
    biz = get_business(business_id)
    biz["members"] = list_members(business_id)
    biz["my_role"] = next(
        (m["role"] for m in biz["members"] if m["user_id"] == user["id"]),
        None,
    )
    return biz


@router.patch("/api/businesses/{business_id}")
def update_my_business(business_id: str, req: BusinessUpdate,
                       user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    return update_business(business_id, user["id"], updates)


@router.delete("/api/businesses/{business_id}")
def delete_my_business(business_id: str, user: dict = Depends(get_current_user)):
    delete_business(business_id, user["id"])
    return {"ok": True}


@router.get("/api/businesses/{business_id}/members")
def list_business_members(business_id: str, user: dict = Depends(get_current_user)):
    assert_member(business_id, user["id"])
    return list_members(business_id)


@router.post("/api/businesses/{business_id}/members")
def add_business_member(business_id: str, req: MemberAdd,
                        user: dict = Depends(get_current_user)):
    add_member(business_id, user["id"], req.user_id, req.role)
    return {"ok": True}


@router.delete("/api/businesses/{business_id}/members/{target_user_id}")
def remove_business_member(business_id: str, target_user_id: str,
                           user: dict = Depends(get_current_user)):
    remove_member(business_id, user["id"], target_user_id)
    return {"ok": True}
