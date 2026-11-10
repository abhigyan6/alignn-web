from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from alignn.domains.eligibility.schemas import EligibilityPolicy
from alignn.domains.eligibility.service import evaluate, profile_evidence
from alignn.domains.identity.service import check_csrf, get_actor, require_verified
from alignn.domains.matching.service import calculate_fit
from alignn.domains.organizations.models import Membership, Organization
from alignn.domains.organizations.service import lock_organization, require_membership
from alignn.errors import DomainError

from .models import Opportunity, SavedOpportunity
from .schemas import (
    OpportunityCreate,
    OpportunityMutation,
    OpportunityOut,
    SearchQuery,
    VersionCommand,
)
from .service import (
    lock_opportunity,
    mutate_opportunity,
    search_opportunities,
    validate_skills,
    visible,
)

router = APIRouter(prefix="/api/v1", tags=["Opportunities"])


def optional_actor(request):
    config = request.app.state.settings
    supplied = (
        request.headers.get("authorization")
        if config.auth_provider == "clerk"
        else request.cookies.get("alignn_session")
    )
    return get_actor(request) if supplied else None


@router.get("/opportunities")
def search(request: Request, query: SearchQuery = Depends()):
    return search_opportunities(request.state.db, optional_actor(request), query)


@router.get("/organizer/opportunities")
def owned(request: Request):
    actor = get_actor(request)
    db = request.state.db
    rows = db.scalars(
        select(Opportunity)
        .join(Membership, Membership.organization_id == Opportunity.organization_id)
        .where(
            Membership.user_id == actor.user_id,
            Membership.role.in_(["OWNER", "MANAGER"]),
            Opportunity.mode == "EXTERNAL",
        )
        .order_by(Opportunity.created_at.desc())
        .limit(100)
    ).all()
    return {"items": [OpportunityOut.model_validate(o) for o in rows]}


@router.post(
    "/organizations/{id}/opportunities",
    status_code=201,
    response_model=OpportunityOut,
    dependencies=[Depends(check_csrf)],
)
def create(id: UUID, data: OpportunityCreate, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    require_membership(db, actor, id, "manage")
    validate_skills(db, data)
    values = data.model_dump(mode="python")
    values["eligibility"] = data.eligibility.model_dump(mode="json")
    o = Opportunity(organization_id=id, organization_name=db.get(Organization, id).name, **values)
    db.add(o)
    db.flush()
    return o


@router.get("/opportunities/{id}", response_model=OpportunityOut)
def detail(id: UUID, request: Request):
    return visible(request.state.db, optional_actor(request), id)


@router.put(
    "/opportunities/{id}", response_model=OpportunityOut, dependencies=[Depends(check_csrf)]
)
def update(id: UUID, data: OpportunityMutation, request: Request):
    return mutate_opportunity(
        request.state.db, get_actor(request), id, data.expected_version, data.opportunity
    )


@router.post(
    "/opportunities/{id}/publish", response_model=OpportunityOut, dependencies=[Depends(check_csrf)]
)
def publish(id: UUID, data: VersionCommand, request: Request):
    actor = require_verified(get_actor(request))
    db = request.state.db
    o = lock_opportunity(db, id)
    require_membership(db, actor, o.organization_id, "manage")
    organization = lock_organization(db, o.organization_id)
    if not organization.verified:
        raise DomainError(
            "organization_unverified", "Your organization must be verified before publishing.", 409
        )
    if o.version != data.expected_version:
        raise DomainError("stale_version", "Reload the latest opportunity.", 409)
    if o.status != "DRAFT":
        raise DomainError("invalid_state", "Only a draft can be published.", 409)
    from alignn.db import utcnow

    if o.registration_closes_at is not None and o.registration_closes_at <= utcnow():
        raise DomainError("deadline_passed", "Registration close must be in the future.", 409)
    o.organization_name = organization.name
    o.status = "PUBLISHED"
    o.version += 1
    return o


@router.post(
    "/opportunities/{id}/cancel", response_model=OpportunityOut, dependencies=[Depends(check_csrf)]
)
def cancel(id: UUID, data: VersionCommand, request: Request):
    db = request.state.db
    o = lock_opportunity(db, id)
    require_membership(db, get_actor(request), o.organization_id, "manage")
    if o.version != data.expected_version:
        raise DomainError("stale_version", "Reload the latest opportunity.", 409)
    o.status = "CANCELLED"
    o.version += 1
    return o


@router.get("/opportunities/{id}/eligibility")
def eligibility(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    o = visible(db, actor, id)
    if o.source_name:
        raise DomainError(
            "eligibility_unstructured",
            "Check eligibility requirements on the original listing.",
            409,
        )
    return {
        **evaluate(
            profile_evidence(db, actor), EligibilityPolicy.model_validate(o.eligibility)
        ).model_dump(),
        "policy_version": o.version,
    }


@router.get("/opportunities/{id}/fit")
def fit(id: UUID, request: Request):
    actor = get_actor(request)
    return calculate_fit(request.state.db, actor.user_id, visible(request.state.db, actor, id))


@router.post("/opportunities/{id}/save", dependencies=[Depends(check_csrf)])
def save(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    visible(db, actor, id)
    from sqlalchemy.dialects.postgresql import insert

    db.execute(
        insert(SavedOpportunity)
        .values(user_id=actor.user_id, opportunity_id=id)
        .on_conflict_do_nothing()
    )
    return {"saved": True}


@router.delete("/opportunities/{id}/save", status_code=204, dependencies=[Depends(check_csrf)])
def unsave(id: UUID, request: Request):
    from sqlalchemy import delete

    actor = get_actor(request)
    request.state.db.execute(
        delete(SavedOpportunity).where(
            SavedOpportunity.user_id == actor.user_id, SavedOpportunity.opportunity_id == id
        )
    )


@router.get("/me/saved")
def saved(request: Request):
    actor = get_actor(request)
    db = request.state.db
    rows = db.scalars(
        select(Opportunity)
        .join(SavedOpportunity)
        .where(
            SavedOpportunity.user_id == actor.user_id,
            Opportunity.status == "PUBLISHED",
            Opportunity.mode == "EXTERNAL",
        )
        .order_by(Opportunity.registration_closes_at)
        .limit(100)
    ).all()
    return {"items": [OpportunityOut.model_validate(o) for o in rows]}
