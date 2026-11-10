from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import Field, field_validator
from sqlalchemy import select

from alignn.audit import AuditRecord
from alignn.db import utcnow
from alignn.domains.identity.schemas import StrictModel
from alignn.domains.identity.service import check_csrf, get_actor, require_admin
from alignn.errors import DomainError
from alignn.jobs.models import Job

router = APIRouter(prefix="/api/v1/admin/jobs", tags=["Operations"])


@router.get("")
def list_jobs(
    request: Request,
    status: Literal["QUEUED", "RUNNING", "FAILED", "DONE", "SKIPPED"] | None = None,
    limit: int = Query(30, ge=1, le=100),
):
    require_admin(get_actor(request))
    query = select(Job).order_by(Job.created_at.desc(), Job.id.desc()).limit(limit)
    if status:
        query = query.where(Job.status == status)
    rows = request.state.db.scalars(query).all()
    return {
        "items": [
            {
                "id": row.id,
                "kind": row.kind,
                "status": row.status,
                "attempts": row.attempts,
                "last_error": row.last_error,
                "run_at": row.run_at,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


class ReplayRequest(StrictModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason", mode="before")
    @classmethod
    def trim_reason(cls, value):
        return value.strip() if isinstance(value, str) else value


@router.post("/{id}/replay", dependencies=[Depends(check_csrf)])
def replay_job(id: UUID, data: ReplayRequest, request: Request):
    actor = require_admin(get_actor(request))
    db = request.state.db
    job = db.scalar(select(Job).where(Job.id == id).with_for_update())
    if not job:
        raise DomainError("not_found", "Job not found.", 404)
    if job.status != "FAILED" or not job.payload:
        raise DomainError(
            "invalid_job_state", "Only failed jobs with recoverable data can be replayed.", 409
        )
    if job.expires_at and job.expires_at <= utcnow():
        raise DomainError("job_expired", "This job has expired. Request a new action instead.", 409)
    db.add(
        AuditRecord(
            actor_id=actor.user_id,
            action="job.replay",
            object_id=str(id),
            reason=data.reason,
            details={"previous_attempts": job.attempts},
        )
    )
    job.status = "QUEUED"
    job.attempts = 0
    job.run_at = utcnow()
    job.created_at = utcnow()
    job.lease_until = None
    job.lease_token = None
    return {"id": job.id, "status": job.status}
