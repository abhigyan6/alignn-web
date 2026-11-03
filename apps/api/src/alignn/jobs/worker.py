import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from alignn.adapters.mail import PermanentDeliveryError
from alignn.config import settings
from alignn.db import SessionLocal, utcnow
from alignn.jobs.handlers import Adapters, dispatch
from alignn.jobs.models import Job

logger = logging.getLogger("alignn.worker")


@dataclass(frozen=True)
class JobLease:
    id: UUID
    kind: str
    key: str
    payload: dict
    lease_token: UUID
    attempts: int


class Clock:
    def now(self):
        return utcnow()


def enqueue_job(
    db: Session,
    *,
    kind: str,
    key: str,
    payload: dict,
    run_at: datetime,
    expires_at: datetime | None,
) -> UUID:
    id = db.scalar(
        insert(Job)
        .values(kind=kind, key=key, payload=payload, run_at=run_at, expires_at=expires_at)
        .on_conflict_do_nothing(index_elements=[Job.key])
        .returning(Job.id)
    )
    return id or db.scalar(select(Job.id).where(Job.key == key))


def lease_jobs(db: Session, *, worker_id: str, now: datetime, limit: int) -> list[JobLease]:
    runnable = or_(
        and_(Job.status == "QUEUED", Job.run_at <= now),
        and_(Job.status == "RUNNING", Job.lease_until <= now),
    )
    jobs = db.scalars(
        select(Job)
        .where(runnable)
        .order_by(Job.run_at, Job.id)
        .with_for_update(skip_locked=True)
        .limit(min(max(limit, 1), 100))
    ).all()
    leases = []
    for job in jobs:
        if job.expires_at and job.expires_at <= now:
            job.status = "SKIPPED"
            job.payload = {}
            continue
        if job.attempts >= 5 or now >= job.created_at + timedelta(hours=24):
            job.status = "FAILED"
            job.last_error = "retry_budget_exhausted"
            continue
        job.status = "RUNNING"
        job.attempts += 1
        job.lease_token = uuid4()
        job.lease_until = now + timedelta(seconds=60)
        job.worker_id = worker_id
        leases.append(
            JobLease(job.id, job.kind, job.key, job.payload, job.lease_token, job.attempts)
        )
    db.flush()
    return leases


def complete_lease(db: Session, lease: JobLease) -> bool:
    result = db.execute(
        update(Job)
        .where(Job.id == lease.id, Job.status == "RUNNING", Job.lease_token == lease.lease_token)
        .values(status="DONE", payload={}, lease_until=None)
    )
    return result.rowcount == 1


def heartbeat(db: Session, lease: JobLease, now: datetime) -> bool:
    result = db.execute(
        update(Job)
        .where(
            Job.id == lease.id,
            Job.status == "RUNNING",
            Job.lease_token == lease.lease_token,
            Job.lease_until > now,
        )
        .values(lease_until=now + timedelta(seconds=60))
    )
    return result.rowcount == 1


def fail_lease(db: Session, lease: JobLease, *, code: str, permanent: bool, now: datetime):
    status = "FAILED" if permanent or lease.attempts >= 5 else "QUEUED"
    delay = min(3600, 15 * 2 ** (lease.attempts - 1)) + random.uniform(0, 10)
    db.execute(
        update(Job)
        .where(Job.id == lease.id, Job.status == "RUNNING", Job.lease_token == lease.lease_token)
        .values(
            status=status,
            last_error=code[:100],
            run_at=now + timedelta(seconds=delay),
            lease_until=None,
        )
    )


def process_lease(lease: JobLease, adapters: Adapters, clock: Clock) -> None:
    with SessionLocal.begin() as db:
        if not heartbeat(db, lease, clock.now()):
            return
        job = db.get(Job, lease.id)
        if job.expires_at and job.expires_at <= clock.now():
            job.status = "SKIPPED"
            job.payload = {}
            return
    try:
        dispatch(lease.kind, lease.payload, adapters, lease.key)
    except PermanentDeliveryError as exc:
        with SessionLocal.begin() as db:
            fail_lease(db, lease, code=str(exc), permanent=True, now=clock.now())
    except Exception:
        # Payloads can contain private mail links. Never log provider exceptions or payloads.
        logger.warning("Job delivery failed", extra={"job_id": str(lease.id)})
        with SessionLocal.begin() as db:
            fail_lease(db, lease, code="provider_failure", permanent=False, now=clock.now())
    else:
        with SessionLocal.begin() as db:
            complete_lease(db, lease)


def run_once(adapters: Adapters, *, worker_id: str) -> int:
    # Sequential dispatch leases one item so later jobs do not expire while waiting.
    with SessionLocal.begin() as db:
        leases = lease_jobs(db, worker_id=worker_id, now=utcnow(), limit=1)
    for lease in leases:
        process_lease(lease, adapters, Clock())
    return len(leases)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Alignn background worker")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    adapters = Adapters.configured(settings)
    worker_id = str(uuid4())
    while True:
        count = run_once(adapters, worker_id=worker_id)
        if args.once:
            break
        if not count:
            time.sleep(1)


if __name__ == "__main__":
    main()
