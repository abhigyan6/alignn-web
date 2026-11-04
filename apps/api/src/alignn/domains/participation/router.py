from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select

from alignn.db import utcnow
from alignn.domains.files.models import ConsentGrant
from alignn.domains.identity.models import User
from alignn.domains.identity.service import check_csrf, get_actor
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.opportunities.service import lock_opportunity
from alignn.domains.organizations.service import require_membership, require_verified_organization
from alignn.errors import DomainError

from .models import EventConsent, Registration, RegistrationMember
from .schemas import ConsentUpdate, RegistrationCreate, RegistrationOut
from .service import register, registration_out, set_consent, withdraw

router = APIRouter(prefix="/api/v1", tags=["Participation"])


class Clock:
    def now(self):
        return utcnow()


@router.post(
    "/opportunities/{id}/registrations",
    response_model=RegistrationOut,
    status_code=201,
    dependencies=[Depends(check_csrf)],
)
def create(
    id: UUID,
    data: RegistrationCreate,
    request: Request,
    idempotency_key: str = Header(min_length=8, max_length=128),
):
    result = register(request.state.db, get_actor(request), id, data, idempotency_key, Clock())
    return {**result, "request_id": request.state.request_id}


@router.post("/registrations/{id}/withdraw", dependencies=[Depends(check_csrf)])
def withdrawal(id: UUID, request: Request):
    return withdraw(request.state.db, get_actor(request), id, Clock())


@router.get("/me/registrations")
def mine(request: Request):
    actor = get_actor(request)
    db = request.state.db
    rows = db.execute(
        select(Registration, Opportunity)
        .join(RegistrationMember, RegistrationMember.registration_id == Registration.id)
        .join(Opportunity, Opportunity.id == Registration.opportunity_id)
        .where(RegistrationMember.user_id == actor.user_id)
        .order_by(Registration.created_at.desc())
        .limit(100)
    ).all()
    return {
        "items": [
            {
                **registration_out(db, r),
                "title": o.title,
                "starts_at": o.starts_at,
                "registration_closes_at": o.registration_closes_at,
            }
            for r, o in rows
        ]
    }


@router.put("/opportunities/{id}/consent", dependencies=[Depends(check_csrf)])
def consent(id: UUID, data: ConsentUpdate, request: Request):
    actor = get_actor(request)
    db = request.state.db
    lock_opportunity(db, id)
    set_consent(db, actor, id, data.contact)
    return {"contact": data.contact}


@router.get("/organizer/opportunities/{id}/registrations")
def organizer(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    o = db.get(Opportunity, id)
    if not o:
        raise DomainError("not_found", "Opportunity not found.", 404)
    require_membership(db, actor, o.organization_id, "manage")
    require_verified_organization(db, o.organization_id)
    items = []
    for r in db.scalars(
        select(Registration)
        .where(Registration.opportunity_id == id)
        .order_by(Registration.created_at)
        .limit(100)
    ):
        roster = []
        for m in db.scalars(
            select(RegistrationMember)
            .where(RegistrationMember.registration_id == r.id)
            .order_by(RegistrationMember.user_id)
        ):
            c = db.scalar(
                select(EventConsent).where(
                    EventConsent.user_id == m.user_id, EventConsent.opportunity_id == id
                )
            )
            f = db.scalar(
                select(ConsentGrant).where(
                    ConsentGrant.owner_id == m.user_id,
                    ConsentGrant.opportunity_id == id,
                    ~ConsentGrant.revoked,
                )
            )
            roster.append(
                {
                    "user_id": m.user_id,
                    "full_name": m.full_name,
                    "contact": db.get(User, m.user_id).email if c and c.contact else None,
                    "resume_file_id": f.file_id if f else None,
                }
            )
        items.append(
            {
                "id": r.id,
                "status": r.status,
                "team_id": r.team_id,
                "created_at": r.created_at,
                "roster": roster,
            }
        )
    return {"items": items}
