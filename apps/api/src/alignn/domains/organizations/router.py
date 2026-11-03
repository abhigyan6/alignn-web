from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from alignn.audit import AuditRecord
from alignn.db import utcnow
from alignn.domains.identity.models import User
from alignn.domains.identity.service import check_csrf, get_actor, require_admin, require_verified
from alignn.domains.organizations.models import Membership, Organization, OrganizationInvitation
from alignn.domains.organizations.schemas import (
    InvitationCreate,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
    OwnershipTransfer,
)
from alignn.domains.organizations.service import lock_organization, require_membership
from alignn.errors import DomainError
from alignn.jobs.router import ReplayRequest
from alignn.jobs.worker import enqueue_job

router = APIRouter(prefix="/api/v1", tags=["Organizations"])


@router.get("/organizations")
def my_organizations(request: Request):
    actor = get_actor(request)
    rows = request.state.db.execute(
        select(Organization, Membership)
        .join(Membership)
        .where(Membership.user_id == actor.user_id)
        .order_by(Organization.name)
    ).all()
    return {
        "items": [
            {**OrganizationOut.model_validate(o).model_dump(), "role": m.role} for o, m in rows
        ]
    }


@router.post(
    "/organizations",
    response_model=OrganizationOut,
    status_code=201,
    dependencies=[Depends(check_csrf)],
)
def create_organization(data: OrganizationCreate, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    organization = Organization(**data.model_dump())
    db.add(organization)
    db.flush()
    db.add(Membership(organization_id=organization.id, user_id=actor.user_id, role="OWNER"))
    db.add(
        AuditRecord(
            actor_id=actor.user_id,
            action="organization.requested",
            object_id=str(organization.id),
            reason="Organization registration",
        )
    )
    return organization


@router.get("/organizations/{id}", response_model=OrganizationOut)
def organization(id: UUID, request: Request):
    require_membership(request.state.db, get_actor(request), id, "read")
    return request.state.db.get(Organization, id)


@router.patch(
    "/organizations/{id}", response_model=OrganizationOut, dependencies=[Depends(check_csrf)]
)
def edit_organization(id: UUID, data: OrganizationUpdate, request: Request):
    actor = get_actor(request)
    db = request.state.db
    organization = lock_organization(db, id)
    require_membership(db, actor, id, "manage")
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is None:
            raise DomainError("invalid_input", "Organization fields cannot be null.", 422)
        setattr(organization, key, value)
    return organization


@router.get("/organizations/{id}/members")
def members(id: UUID, request: Request):
    db = request.state.db
    require_membership(db, get_actor(request), id, "members")
    rows = db.execute(
        select(Membership, User).join(User).where(Membership.organization_id == id)
    ).all()
    return {"items": [{"user_id": u.id, "full_name": u.full_name, "role": m.role} for m, u in rows]}


@router.post("/organizations/{id}/invitations", status_code=201, dependencies=[Depends(check_csrf)])
def invite(id: UUID, data: InvitationCreate, request: Request):
    actor = get_actor(request)
    db = request.state.db
    lock_organization(db, id)
    require_membership(db, actor, id, "members")
    existing = db.scalar(
        select(OrganizationInvitation).where(
            OrganizationInvitation.organization_id == id,
            OrganizationInvitation.email == data.email,
            ~OrganizationInvitation.accepted,
            OrganizationInvitation.expires_at > utcnow(),
        )
    )
    if existing:
        raise DomainError("already_invited", "An active invitation already exists.", 409)
    invitation = OrganizationInvitation(
        organization_id=id,
        email=data.email,
        role=data.role,
        expires_at=utcnow() + timedelta(hours=72),
    )
    db.add(invitation)
    db.flush()
    enqueue_job(
        db,
        kind="mail",
        key=f"organization-invite-{invitation.id}",
        run_at=utcnow(),
        expires_at=invitation.expires_at,
        payload={
            "to": data.email,
            "subject": "You have an Alignn organization invitation",
            "text": f"Sign in to view and accept your invitation: {request.app.state.settings.public_origin}/invitations",
        },
    )
    return {
        "id": invitation.id,
        "email": invitation.email,
        "role": invitation.role,
        "expires_at": invitation.expires_at,
    }


@router.get("/organization-invitations")
def invitations(request: Request):
    actor = get_actor(request)
    db = request.state.db
    user = db.get(User, actor.user_id)
    rows = db.execute(
        select(OrganizationInvitation, Organization)
        .join(Organization)
        .where(
            OrganizationInvitation.email == user.email,
            ~OrganizationInvitation.accepted,
            OrganizationInvitation.expires_at > utcnow(),
        )
    ).all()
    return {
        "items": [
            {
                "id": i.id,
                "organization_id": o.id,
                "organization_name": o.name,
                "role": i.role,
                "expires_at": i.expires_at,
            }
            for i, o in rows
        ]
    }


@router.post("/organization-invitations/{id}/accept", dependencies=[Depends(check_csrf)])
def accept_invitation(id: UUID, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    user = db.get(User, actor.user_id)
    invitation = db.scalar(
        select(OrganizationInvitation).where(
            OrganizationInvitation.id == id, OrganizationInvitation.email == user.email
        )
    )
    if not invitation:
        raise DomainError("not_found", "Invitation not found.", 404)
    lock_organization(db, invitation.organization_id)
    db.refresh(invitation, with_for_update=True)
    if invitation.accepted or invitation.expires_at <= utcnow():
        raise DomainError("invitation_expired", "This invitation is no longer available.", 409)
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == invitation.organization_id,
            Membership.user_id == actor.user_id,
        )
    )
    if membership:
        raise DomainError("already_member", "You already belong to this organization.", 409)
    db.add(
        Membership(
            organization_id=invitation.organization_id, user_id=actor.user_id, role=invitation.role
        )
    )
    invitation.accepted = True
    db.add(
        AuditRecord(
            actor_id=actor.user_id,
            action="organization.invitation_accepted",
            object_id=str(invitation.organization_id),
            reason="Recipient accepted invitation",
        )
    )
    return {"organization_id": invitation.organization_id, "role": invitation.role}


@router.delete(
    "/organizations/{id}/members/me", status_code=204, dependencies=[Depends(check_csrf)]
)
def leave(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    lock_organization(db, id)
    membership = require_membership(db, actor, id, "read")
    if membership.role == "OWNER":
        raise DomainError("owner_required", "Transfer ownership before leaving.", 409)
    db.delete(membership)
    db.add(
        AuditRecord(
            actor_id=actor.user_id,
            action="organization.left",
            object_id=str(id),
            reason="Member left organization",
        )
    )


@router.post("/organizations/{id}/ownership", dependencies=[Depends(check_csrf)])
def transfer_ownership(id: UUID, data: OwnershipTransfer, request: Request):
    actor = get_actor(request)
    db = request.state.db
    lock_organization(db, id)
    current = require_membership(db, actor, id, "members")
    target = db.scalar(
        select(Membership)
        .join(User)
        .where(
            Membership.organization_id == id,
            Membership.user_id == data.user_id,
            User.is_active,
            User.is_verified,
        )
    )
    if not target or target.user_id == actor.user_id:
        raise DomainError("invalid_owner", "Choose another verified member.", 422)
    current.role = "MANAGER"
    db.flush()
    target.role = "OWNER"
    db.add(
        AuditRecord(
            actor_id=actor.user_id,
            action="organization.ownership_transferred",
            object_id=str(id),
            reason="Owner transferred organization",
            details={"new_owner_id": str(target.user_id)},
        )
    )
    return {"owner_id": target.user_id}


@router.get("/admin/organizations")
def verification_queue(request: Request):
    require_admin(get_actor(request))
    rows = request.state.db.scalars(
        select(Organization)
        .where(~Organization.verified)
        .order_by(Organization.created_at)
        .limit(100)
    ).all()
    return {"items": [OrganizationOut.model_validate(row) for row in rows]}


@router.post(
    "/admin/organizations/{id}/verify",
    response_model=OrganizationOut,
    dependencies=[Depends(check_csrf)],
)
def verify_organization(id: UUID, data: ReplayRequest, request: Request):
    actor = require_admin(get_actor(request))
    db = request.state.db
    organization = lock_organization(db, id)
    organization.verified = True
    organization.verified_at = utcnow()
    db.add(
        AuditRecord(
            actor_id=actor.user_id,
            action="organization.verified",
            object_id=str(id),
            reason=data.reason,
        )
    )
    return organization
