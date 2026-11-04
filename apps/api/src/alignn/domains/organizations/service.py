from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from alignn.domains.identity.schemas import Actor
from alignn.domains.organizations.models import Membership, Organization
from alignn.errors import DomainError

CAPABILITIES = {
    "read": {"OWNER", "MANAGER", "REVIEWER"},
    "manage": {"OWNER", "MANAGER"},
    "members": {"OWNER"},
    "review": {"OWNER", "MANAGER", "REVIEWER"},
}


def require_membership(
    db: Session, actor: Actor, organization_id: UUID, capability: str
) -> Membership:
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == actor.user_id, Membership.organization_id == organization_id
        )
    )
    if not membership:
        raise DomainError("not_found", "Organization not found.", 404)
    if membership.role not in CAPABILITIES.get(capability, set()):
        raise DomainError("forbidden", "Your role does not allow this action.", 403)
    return membership


def lock_organization(db: Session, id: UUID) -> Organization:
    organization = db.scalar(select(Organization).where(Organization.id == id).with_for_update())
    if not organization:
        raise DomainError("not_found", "Organization not found.", 404)
    return organization


def require_verified_organization(db: Session, organization_id: UUID) -> Organization:
    organization = db.get(Organization, organization_id)
    if not organization or not organization.verified:
        raise DomainError(
            "organization_unverified",
            "Organization verification is required for participant data access.",
            403,
        )
    return organization
