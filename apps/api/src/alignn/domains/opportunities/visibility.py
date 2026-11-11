"""Shared discovery boundaries; history records are never deleted here."""

from sqlalchemy import or_, select

from .models import Opportunity


def active_filters(now):
    return (
        Opportunity.status == "PUBLISHED",
        Opportunity.mode == "EXTERNAL",
        or_(Opportunity.source_name.is_(None), Opportunity.source_name != "Remotive"),
        or_(Opportunity.registration_closes_at.is_(None), Opportunity.registration_closes_at > now),
        or_(Opportunity.ends_at.is_(None), Opportunity.ends_at > now),
    )


def expire_opportunities(db, now, limit=500):
    rows = db.scalars(
        select(Opportunity)
        .where(
            Opportunity.status == "PUBLISHED",
            Opportunity.mode == "EXTERNAL",
            or_(
                Opportunity.source_name == "Remotive",
                Opportunity.registration_closes_at <= now,
                Opportunity.ends_at <= now,
            ),
        )
        .order_by(Opportunity.id)
        .with_for_update(skip_locked=True)
        .limit(limit)
    ).all()
    for row in rows:
        # Evaluate current row under lock: queued payloads cannot close extensions.
        row.closure_reason = (
            "source_retired"
            if row.source_name == "Remotive"
            else "registration_elapsed"
            if row.registration_closes_at and row.registration_closes_at <= now
            else "event_ended"
        )
        row.status = "CLOSED"
        row.version += 1
    return len(rows)
