from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from alignn.config import settings
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.participation.models import (
    EligibilitySnapshot,
    IdempotencyRecord,
    Registration,
    RegistrationMember,
)

BATCH_SIZE = 500


def prune_retired_event_data(db: Session, now: datetime) -> int:
    expired_replays = (
        select(IdempotencyRecord.id)
        .where(IdempotencyRecord.expires_at <= now)
        .order_by(IdempotencyRecord.expires_at, IdempotencyRecord.id)
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    deleted = db.execute(
        delete(IdempotencyRecord).where(IdempotencyRecord.id.in_(expired_replays))
    ).rowcount

    cutoff = now - timedelta(days=settings.retired_event_evidence_retention_days)
    snapshots = db.scalars(
        select(EligibilitySnapshot.id)
        .join(Opportunity)
        .where(
            Opportunity.mode == "HOSTED",
            func.greatest(Opportunity.ends_at, EligibilitySnapshot.created_at) <= cutoff,
            EligibilitySnapshot.evidence != [],
        )
        .order_by(EligibilitySnapshot.created_at, EligibilitySnapshot.id)
        .limit(BATCH_SIZE)
        .with_for_update(of=EligibilitySnapshot, skip_locked=True)
    ).all()
    if snapshots:
        registration_ids = select(Registration.id).where(
            Registration.eligibility_snapshot_id.in_(snapshots)
        )
        db.execute(
            update(RegistrationMember)
            .where(RegistrationMember.registration_id.in_(registration_ids))
            .values(admission_evidence={})
        )
        db.execute(
            update(EligibilitySnapshot)
            .where(EligibilitySnapshot.id.in_(snapshots))
            .values(evidence=[])
        )
    return deleted + len(snapshots)
