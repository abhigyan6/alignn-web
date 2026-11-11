import json
from copy import deepcopy
from datetime import timedelta
from threading import Event
from uuid import uuid4

import httpx
import pytest
from scrapy.http import HtmlResponse
from sqlalchemy import select

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.devfolio import (
    SOURCE,
    event_url,
    index_events,
    next_data,
    normalize_event,
    sync_devfolio,
)
from alignn.domains.opportunities.greenhouse import normalize_intern, sync_board
from alignn.domains.opportunities.models import Opportunity
from alignn.jobs import worker


def event():
    now = utcnow()
    return dict(
        uuid=uuid4().hex,
        slug="test-event",
        country="India",
        city="Bhopal",
        type="HACKATHON",
        name="Student buildathon",
        desc="Build useful Python projects.",
        is_online=False,
        starts_at=(now + timedelta(days=8)).isoformat(),
        ends_at=(now + timedelta(days=9)).isoformat(),
        settings={"reg_ends_at": (now + timedelta(days=7)).isoformat()},
        participants_details=[{"email": "private@alignn.test"}],
    )


def normalized(raw):
    from uuid import UUID

    return normalize_event(raw, str(UUID(raw["uuid"])), event_url(raw["slug"]), utcnow())


def manifest(raw):
    return {"index_valid": True, "rows": [normalized(raw)], "detail_failures": 0}


def test_country_dates_and_pii_are_not_invented():
    raw = event()
    row = normalized(raw)
    assert row["location"] == "Bhopal, India"
    assert row["registration_closes_at"] == raw["settings"]["reg_ends_at"].replace("+00:00", "Z")
    assert "private@" not in json.dumps(row)
    assert "eligibility" not in row
    for country in [None, "", "United States"]:
        assert normalized({**raw, "country": country, "timezone": "Asia/Calcutta"}) is None
    assert normalized({**raw, "settings": {}})["registration_closes_at"] is None
    expired = {**raw, "settings": {"reg_ends_at": (utcnow() - timedelta(days=1)).isoformat()}}
    assert normalized(expired) is None
    with pytest.raises(ValueError):
        normalize_event(raw, str(uuid4()), event_url(raw["slug"]), utcnow())
    with pytest.raises(ValueError):
        event_url("evil.com/@localhost")


def test_source_structure_and_duplicates_fail_closed():
    with pytest.raises(ValueError):
        next_data(HtmlResponse(url="https://devfolio.co/hackathons", body=b"<h1>Bot check</h1>"))
    raw = event()
    page = {
        "dehydratedState": {
            "queries": [
                {
                    "queryKey": "fetchAllHackathonTypes",
                    "state": {"data": {"open_hackathons": [raw, raw]}},
                }
            ]
        }
    }
    with pytest.raises(ValueError):
        index_events(page)


def test_partial_catalog_dedup_update_and_failure_preserve():
    raw = event()
    assert sync_devfolio(lambda: manifest(raw))["imported"] == 1
    assert sync_devfolio(lambda: pytest.fail("throttled fetch"))["status"] == "throttled"
    with SessionLocal.begin() as db:
        first = db.scalar(select(Opportunity))
        identity = first.id
        first.source_checked_at = utcnow() - timedelta(hours=7)
    newer = deepcopy(raw)
    newer["settings"]["reg_ends_at"] = (utcnow() + timedelta(days=6)).isoformat()
    sync_devfolio(lambda: manifest(newer))
    with SessionLocal.begin() as db:
        row = db.get(Opportunity, identity)
        assert row.version == 2 and row.deadline_version == 2
        row.source_checked_at = utcnow() - timedelta(hours=7)
    with pytest.raises(ValueError):
        sync_devfolio(lambda: {"index_valid": True, "rows": []})
    another = {**event(), "slug": "another-event"}
    sync_devfolio(lambda: manifest(another))
    with SessionLocal() as db:
        assert db.get(Opportunity, identity).status == "PUBLISHED"
        assert (
            len(db.scalars(select(Opportunity).where(Opportunity.source_name == SOURCE)).all()) == 2
        )


def internship(id=1):
    return dict(
        id=id,
        title="Software Engineer, Intern",
        location={"name": "Bengaluru"},
        absolute_url=f"https://stripe.com/jobs/search?gh_jid={id}",
        content="&lt;p&gt;Build Python applications.&lt;/p&gt;",
    )


def board_client(rows, total=None):
    return httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"jobs": rows, "meta": {"total": len(rows) if total is None else total}}
            )
        )
    )


def test_internship_location_and_word_boundaries():
    raw = internship()
    row = normalize_intern(raw, "stripe")
    assert row["kind"] == "INTERNSHIP" and row["registration_closes_at"] is None
    assert "<p>" not in row["description"]
    assert normalize_intern({**raw, "title": "Manager, Internal Systems"}, "stripe") is None
    assert normalize_intern({**raw, "location": {"name": "Remote"}}, "stripe") is None
    with pytest.raises(ValueError):
        normalize_intern({**raw, "absolute_url": "http://localhost/secret"}, "stripe")


def test_employer_snapshot_closes_only_after_complete_feed():
    with board_client([internship()]) as http:
        sync_board("stripe", http)
    with SessionLocal.begin() as db:
        first = db.scalar(select(Opportunity))
        identity = first.id
        first.source_checked_at = utcnow() - timedelta(hours=7)
    with board_client([], total=1) as http, pytest.raises(ValueError):
        sync_board("stripe", http)
    with SessionLocal() as db:
        assert db.get(Opportunity, identity).status == "PUBLISHED"
    with board_client([]) as http:
        assert sync_board("stripe", http)["imported"] == 0
    with SessionLocal() as db:
        assert db.get(Opportunity, identity).status == "CLOSED"


def test_lease_renewal_uses_separate_transactions(monkeypatch):
    lease = object()
    calls = []

    class Stop:
        def wait(self, seconds):
            calls.append(seconds)
            return len(calls) > 1

    monkeypatch.setattr(worker, "heartbeat", lambda db, item, now: item is lease)
    worker.renew_lease(lease, worker.Clock(), Stop())
    assert calls == [20, 20]


def test_process_lease_stops_heartbeat_after_dispatch(monkeypatch):
    # Existing jobs tests cover lease token ownership; verify renewal cleanup on errors.
    from alignn.jobs.models import Job

    now = utcnow()
    with SessionLocal.begin() as db:
        worker.enqueue_job(
            db,
            kind="ingest_devfolio",
            key="test-renewal",
            payload={},
            run_at=now,
            expires_at=now + timedelta(hours=1),
        )
    with SessionLocal.begin() as db:
        lease = worker.lease_jobs(db, worker_id="test", now=now, limit=1)[0]
    stopped = Event()

    def renew(item, clock, stop):
        stop.wait(5)
        if stop.is_set():
            stopped.set()

    monkeypatch.setattr(worker, "renew_lease", renew)
    monkeypatch.setattr(worker, "dispatch", lambda *args: (_ for _ in ()).throw(ValueError()))
    worker.process_lease(lease, None, worker.Clock())
    assert stopped.is_set()
    with SessionLocal() as db:
        assert db.get(Job, lease.id).status == "QUEUED"


@pytest.mark.parametrize("source", ["devfolio", "greenhouse"])
def test_unchanged_sync_keeps_version_and_inferred_skills(source):
    from alignn.domains.profiles.models import Skill

    with SessionLocal.begin() as db:
        if not db.scalar(select(Skill).where(Skill.key == "python")):
            db.add(Skill(key="python", name="Python", aliases=[], category="technical"))
    raw = event()

    def sync():
        if source == "devfolio":
            return sync_devfolio(lambda: manifest(raw))
        with board_client([internship()]) as http:
            return sync_board("stripe", http)

    sync()
    with SessionLocal.begin() as db:
        row = db.scalar(select(Opportunity))
        assert "python" in row.preferred_skills
        version = row.version
        row.source_checked_at = utcnow() - timedelta(hours=7)
    sync()
    with SessionLocal() as db:
        row = db.scalar(select(Opportunity))
        assert row.version == version
        assert "python" in row.preferred_skills


def test_malformed_internship_preserves_existing_catalog():
    with board_client([internship()]) as http:
        sync_board("stripe", http)
    with SessionLocal.begin() as db:
        db.scalar(select(Opportunity)).source_checked_at = utcnow() - timedelta(hours=7)
    with board_client([{**internship(), "location": None}]) as http, pytest.raises(ValueError):
        sync_board("stripe", http)
    with SessionLocal() as db:
        assert db.scalar(select(Opportunity)).status == "PUBLISHED"
