"""Minute cadence for registered domain scheduling functions."""

import time

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.ingestion import schedule_ingestion
from alignn.jobs.retention import prune_retired_event_data

SCHEDULES = [schedule_ingestion, prune_retired_event_data]


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
