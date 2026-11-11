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

    from alignn.config import settings
    from alignn.jobs.worker import enqueue_job
    from alignn_scraper.registry import SOURCES

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


SCHEDULES = [schedule_ingestion, prune_retired_event_data, expire_catalog, schedule_scraper]


def tick():
    with SessionLocal.begin() as db:
        now = utcnow()
        return sum(schedule(db, now) for schedule in SCHEDULES)


def main():
    while True:
        tick()
        time.sleep(60)


if __name__ == "__main__":
    main()
