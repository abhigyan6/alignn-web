from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import Field, field_validator
from sqlalchemy import delete, func, select

from alignn.db import utcnow
from alignn.domains.identity.models import User
from alignn.domains.identity.schemas import Signup, StrictModel
from alignn.domains.identity.service import check_csrf, get_actor, require_verified
from alignn.domains.opportunities.service import lock_opportunity
from alignn.errors import DomainError
from alignn.jobs.worker import enqueue_job

from .models import Team, TeamInvitation, TeamMember
from .service import lock_team, open_event, require_team_member, team_out, unlocked

router = APIRouter(prefix="/api/v1", tags=["Teams"])


class TeamCreate(StrictModel):
    name: str = Field(min_length=2, max_length=100)


class InviteCreate(StrictModel):
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def email_value(cls, v):
        return Signup.normalize_email(v)


@router.post("/opportunities/{id}/teams", status_code=201, dependencies=[Depends(check_csrf)])
def create(id: UUID, data: TeamCreate, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    o = lock_opportunity(db, id)
    open_event(o)
    if o.team_max <= 1:
        raise DomainError("individual_event", "This event uses individual registration.", 409)
    t = Team(opportunity_id=id, captain_id=actor.user_id, name=data.name)
    db.add(t)
    db.flush()
    db.add(TeamMember(opportunity_id=id, team_id=t.id, user_id=actor.user_id))
    db.flush()
    return team_out(db, t)


@router.get("/me/teams")
def mine(request: Request):
    actor = get_actor(request)
    db = request.state.db
    return {
        "items": [
            team_out(db, t)
            for t in db.scalars(
                select(Team)
                .join(TeamMember)
                .where(TeamMember.user_id == actor.user_id)
                .order_by(Team.created_at.desc())
                .limit(100)
            )
        ]
    }


@router.get("/teams/{id}")
def detail(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    t = db.get(Team, id)
    if not t:
        raise DomainError("not_found", "Team not found.", 404)
    require_team_member(db, actor, t)
    return team_out(db, t)


@router.post("/teams/{id}/invitations", status_code=201, dependencies=[Depends(check_csrf)])
def invite(id: UUID, data: InviteCreate, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    o, t = lock_team(db, id)
    require_team_member(db, actor, t, captain=True)
    open_event(o)
    unlocked(t)
    if db.scalar(
        select(TeamInvitation).where(
            TeamInvitation.team_id == id,
            TeamInvitation.email == data.email,
            TeamInvitation.status == "PENDING",
            TeamInvitation.expires_at > utcnow(),
        )
    ):
        raise DomainError("already_invited", "An active invitation already exists.", 409)
    invite = TeamInvitation(
        team_id=id,
        email=data.email,
        expires_at=min(utcnow() + timedelta(hours=72), o.registration_closes_at),
    )
    db.add(invite)
    db.flush()
    enqueue_job(
        db,
        kind="mail",
        key=f"team-invite-{invite.id}",
        payload={
            "to": data.email,
            "subject": "Join your team on Alignn",
            "text": f"View your invitation: {request.app.state.settings.public_origin}/invitations",
        },
        run_at=utcnow(),
        expires_at=invite.expires_at,
    )
    return {"id": invite.id, "expires_at": invite.expires_at, "email": invite.email}


@router.get("/team-invitations")
def invitations(request: Request):
    actor = get_actor(request)
    db = request.state.db
    user = db.get(User, actor.user_id)
    return {
        "items": [
            {
                "id": i.id,
                "team_id": t.id,
                "team_name": t.name,
                "opportunity_id": t.opportunity_id,
                "expires_at": i.expires_at,
            }
            for i, t in db.execute(
                select(TeamInvitation, Team)
                .join(Team)
                .where(
                    TeamInvitation.email == user.email,
                    TeamInvitation.status == "PENDING",
                    TeamInvitation.expires_at > utcnow(),
                )
                .limit(100)
            )
        ]
    }


@router.post("/team-invitations/{id}/accept", dependencies=[Depends(check_csrf)])
def accept(id: UUID, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    user = db.get(User, actor.user_id)
    i = db.scalar(
        select(TeamInvitation).where(TeamInvitation.id == id, TeamInvitation.email == user.email)
    )
    if not i:
        raise DomainError("not_found", "Invitation not found.", 404)
    o, t = lock_team(db, i.team_id)
    open_event(o)
    unlocked(t)
    db.refresh(i, with_for_update=True)
    if i.status != "PENDING" or i.expires_at <= utcnow():
        raise DomainError("invitation_expired", "Invitation has expired or was already used.", 409)
    count = db.scalar(
        select(func.count()).select_from(TeamMember).where(TeamMember.team_id == t.id)
    )
    if count >= o.team_max:
        raise DomainError("team_full", "This team is full.", 409)
    db.add(TeamMember(team_id=t.id, opportunity_id=o.id, user_id=actor.user_id))
    i.status = "ACCEPTED"
    db.flush()
    return team_out(db, t)


@router.post("/team-invitations/{id}/decline", dependencies=[Depends(check_csrf)])
def decline(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    user = db.get(User, actor.user_id)
    i = db.scalar(
        select(TeamInvitation).where(TeamInvitation.id == id, TeamInvitation.email == user.email)
    )
    if not i:
        raise DomainError("not_found", "Invitation not found.", 404)
    lock_team(db, i.team_id)
    db.refresh(i, with_for_update=True)
    if i.status != "PENDING":
        raise DomainError("invitation_used", "Invitation is no longer pending.", 409)
    i.status = "DECLINED"
    return {"declined": True}


@router.delete("/teams/{id}/members/me", status_code=204, dependencies=[Depends(check_csrf)])
def leave(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    o, t = lock_team(db, id)
    require_team_member(db, actor, t)
    open_event(o)
    unlocked(t)
    if t.captain_id == actor.user_id:
        raise DomainError("captain_required", "The captain cannot leave an active team.", 409)
    db.execute(
        delete(TeamMember).where(TeamMember.team_id == id, TeamMember.user_id == actor.user_id)
    )


@router.delete(
    "/teams/{id}/invitations/{invitation_id}", status_code=204, dependencies=[Depends(check_csrf)]
)
def revoke_invitation(id: UUID, invitation_id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    o, t = lock_team(db, id)
    require_team_member(db, actor, t, captain=True)
    open_event(o)
    unlocked(t)
    i = db.get(TeamInvitation, invitation_id)
    if not i or i.team_id != id:
        raise DomainError("not_found", "Invitation not found.", 404)
    i.status = "REVOKED"
