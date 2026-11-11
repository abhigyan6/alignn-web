"""Minute cadence for registered domain scheduling functions."""

import time

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.ingestion import schedule_ingestion
from alignn.jobs.retention import prune_retired_event_data


def expire_catalog(db, now):
    from alignn.domains.opportunities.visibility import expire_opportunities

    return expire_opportunities(db, now)


def schedule_scraper(db, now):
    from datetime import timedelta

    from alignn_scraper.registry import SOURCES

    from alignn.config import settings
    from alignn.jobs.worker import enqueue_job

    if not settings.scraper_sync_enabled:
        return 0
    enqueue_job(
        db,
        kind="poll_scraper",
        key=f"scraper-poll-{now:%Y%m%d%H%M}",
        payload={},
        run_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    for source, spec in SOURCES.items():
        if spec.status != "enabled":
            continue
        enqueue_job(
            db,
            kind="recheck_scraper",
            key=f"scraper-recheck-{source}-{now.date()}-{now.hour // 6}",
            payload={"source": source},
            run_at=now,
            expires_at=now + timedelta(hours=6),
        )
    return 1


def prune_scraper_metadata(db, now):
    from datetime import timedelta

    from sqlalchemy import delete, select, update

    from alignn.domains.opportunities.ingestion_models import ImportReceipt
    from alignn.jobs.models import Job

    abandoned = (
        select(ImportReceipt.id)
        .where(
            ImportReceipt.state.in_(["DISCOVERED", "IMPORTING", "RETRYABLE"]),
            ImportReceipt.created_at < now - timedelta(hours=24),
        )
        .order_by(ImportReceipt.created_at)
        .with_for_update(skip_locked=True)
        .limit(500)
    )
    db.execute(
        update(ImportReceipt)
        .where(ImportReceipt.id.in_(abandoned))
        .values(state="FAILED", error="retry_window_elapsed")
    )
    receipts = (
        select(ImportReceipt.id)
        .where(
            ImportReceipt.created_at < now - timedelta(days=30),
            ImportReceipt.state.in_(["APPLIED", "REJECTED", "FAILED"]),
        )
        .order_by(ImportReceipt.created_at)
        .with_for_update(skip_locked=True)
        .limit(500)
    )
    jobs = (
        select(Job.id)
        .where(
            Job.kind.in_(["poll_scraper", "import_scraper", "recheck_scraper"]),
            Job.status.in_(["DONE", "FAILED", "SKIPPED"]),
            Job.created_at < now - timedelta(days=7),
        )
        .order_by(Job.created_at)
        .with_for_update(skip_locked=True)
        .limit(500)
    )
    return (
        db.execute(delete(ImportReceipt).where(ImportReceipt.id.in_(receipts))).rowcount
        + db.execute(delete(Job).where(Job.id.in_(jobs))).rowcount
    )


SCHEDULES = [
    prune_scraper_metadata,
    schedule_ingestion,
    prune_retired_event_data,
    expire_catalog,
    schedule_scraper,
]


def tick():
    from alignn.model_registry import load_models

    load_models()
    with SessionLocal.begin() as db:
        now = utcnow()
        return sum(schedule(db, now) for schedule in SCHEDULES)


def main():
    while True:
        tick()
        time.sleep(60)


if __name__ == "__main__":
    main()
