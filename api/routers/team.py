"""
Team management — invite + accept flow plus the shared activity feed.

The preview endpoint is intentionally public so somebody who hasn't
signed up yet can still see what business they're being invited to.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import get_current_context, get_current_user
from api import team as _team

router = APIRouter(tags=["team"])


class InviteCreate(BaseModel):
    email: str
    role: str = "member"


class AcceptInvite(BaseModel):
    token: str


@router.get("/api/team/invites")
def list_team_invites(include_accepted: bool = False,
                      ctx: dict = Depends(get_current_context)):
    from api.businesses import assert_member
    assert_member(ctx["business_id"], ctx["user"]["id"])
    return _team.list_invites(ctx["business_id"], include_accepted=include_accepted)


@router.post("/api/team/invites")
def create_team_invite(req: InviteCreate, ctx: dict = Depends(get_current_context)):
    return _team.create_invite(
        ctx["business_id"], ctx["user"]["id"],
        email=req.email, role=req.role,
    )


@router.delete("/api/team/invites/{token}")
def revoke_team_invite(token: str, ctx: dict = Depends(get_current_context)):
    _team.revoke_invite(ctx["business_id"], ctx["user"]["id"], token)
    return {"ok": True}


# Public — no auth, so someone without an account can see what they're joining
@router.get("/api/team/invites/preview")
def preview_invite(token: str):
    return _team.get_invite_preview(token)


@router.post("/api/team/invites/accept")
def accept_team_invite(body: AcceptInvite, user: dict = Depends(get_current_user)):
    return _team.accept_invite(body.token, user["id"], user["email"])


@router.get("/api/team/activity")
def activity_feed_api(limit: int = 60, ctx: dict = Depends(get_current_context)):
    return _team.activity_feed(ctx["business_id"], limit=limit)
