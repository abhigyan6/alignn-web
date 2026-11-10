from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy import select

from alignn.domains.identity.schemas import StrictModel
from alignn.domains.identity.service import check_csrf, get_actor
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.opportunities.service import visible
from alignn.errors import DomainError

from .models import Application, ApplicationEvent

router = APIRouter(prefix="/api/v1", tags=["External applications"])


class ApplicationCreate(StrictModel):
    opportunity_id: UUID


class ApplicationEventCreate(StrictModel):
    status: Literal["SAVED", "APPLIED", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"]
    note: str = Field("", max_length=2000)


def output(a, o):
    return {
        "id": a.id,
        "opportunity_id": a.opportunity_id,
        "title": o.title,
        "organization_name": o.organization_name,
        "status": a.status,
        "created_at": a.created_at,
        "registration_closes_at": o.registration_closes_at,
    }


@router.post("/applications", status_code=201, dependencies=[Depends(check_csrf)])
def create(data: ApplicationCreate, request: Request):
    actor = get_actor(request)
    db = request.state.db
    o = visible(db, actor, data.opportunity_id)
    a = db.scalar(
        select(Application).where(
            Application.user_id == actor.user_id, Application.opportunity_id == o.id
        )
    )
    if not a:
        a = Application(user_id=actor.user_id, opportunity_id=o.id)
        db.add(a)
        db.flush()
        db.add(ApplicationEvent(application_id=a.id, status="SAVED"))
    return output(a, o)


def record_application_event(db, actor, application_id, data):
    a = db.scalar(
        select(Application)
        .where(Application.id == application_id, Application.user_id == actor.user_id)
        .with_for_update()
    )
    if not a:
        raise DomainError("not_found", "Application not found.", 404)
    a.status = data.status
    db.add(ApplicationEvent(application_id=a.id, **data.model_dump()))
    db.flush()
    return output(a, db.get(Opportunity, a.opportunity_id))


@router.post("/applications/{id}/events", status_code=201, dependencies=[Depends(check_csrf)])
def event(id: UUID, data: ApplicationEventCreate, request: Request):
    return record_application_event(request.state.db, get_actor(request), id, data)


@router.get("/me/applications")
def listing(request: Request):
    actor = get_actor(request)
    db = request.state.db
    return {
        "items": [
            output(a, o)
            for a, o in db.execute(
                select(Application, Opportunity)
                .join(Opportunity)
                .where(Application.user_id == actor.user_id)
                .order_by(Application.created_at.desc())
                .limit(100)
            )
        ]
    }


@router.get("/applications/{id}/events")
def history(id: UUID, request: Request):
    actor = get_actor(request)
    db = request.state.db
    a = db.get(Application, id)
    if not a or a.user_id != actor.user_id:
        raise DomainError("not_found", "Application not found.", 404)
    return {
        "items": [
            {"status": e.status, "note": e.note, "created_at": e.created_at}
            for e in db.scalars(
                select(ApplicationEvent)
                .where(ApplicationEvent.application_id == id)
                .order_by(ApplicationEvent.created_at)
            )
        ]
    }
