from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.models import Opportunity, SavedOpportunity
from alignn.domains.opportunities.schemas import SearchQuery
from alignn.domains.opportunities.service import search_opportunities
from alignn.domains.organizations.models import Organization


def add_opportunity(db, **kwargs):
    org = Organization(name="Source", verified=False)
    db.add(org)
    db.flush()
    row = Opportunity(
        organization_id=org.id,
        title="Build useful technology",
        description="A public Indian student hackathon.",
        organization_name="Source",
        kind="HACKATHON",
        mode="EXTERNAL",
        status="PUBLISHED",
        apply_url="https://hackindia.org/2026/test",
        source_name="HackIndia",
        source_id=uuid4().hex,
        **kwargs,
    )
    db.add(row)
    db.flush()
    return row


def test_discovery_hides_ended_and_retired_but_keeps_ongoing():
    with SessionLocal.begin() as db:
        ended = add_opportunity(db, ends_at=utcnow() - timedelta(seconds=1))
        live = add_opportunity(
            db, starts_at=utcnow() - timedelta(days=1), ends_at=utcnow() + timedelta(days=1)
        )
        retired = add_opportunity(db)
        retired.source_name = "Remotive"
        found = search_opportunities(db, None, SearchQuery())["items"]
        assert [item.id for item in found] == [live.id]
        assert db.get(Opportunity, ended.id) is not None


def test_retirement_and_expiry_preserve_saved_history(make_user):
    from alignn.domains.opportunities.visibility import expire_opportunities

    user = make_user()
    with SessionLocal.begin() as db:
        row = add_opportunity(db)
        row.source_name = "Remotive"
        db.add(SavedOpportunity(user_id=user.id, opportunity_id=row.id))
        ended = add_opportunity(db, ends_at=utcnow() - timedelta(days=1))
        assert expire_opportunities(db, utcnow()) == 2
        assert row.status == ended.status == "CLOSED"
        assert db.scalar(select(SavedOpportunity)).opportunity_id == row.id
        assert expire_opportunities(db, utcnow()) == 0


def test_remotive_jobs_never_fetch_and_are_not_scheduled(monkeypatch):
    import httpx

    from alignn.domains.opportunities.ingestion import schedule_ingestion, sync_remotive
    from alignn.jobs.handlers import dispatch
    from alignn.jobs.models import Job

    monkeypatch.setattr(
        httpx.Client,
        "stream",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("Retired source must not fetch")),
    )
    assert sync_remotive()["status"] == "retired"
    dispatch("ingest_remotive", {}, None, "old-job")
    with SessionLocal.begin() as db:
        schedule_ingestion(db, utcnow())
        assert not db.scalar(select(Job).where(Job.kind == "ingest_remotive"))


def observation(source="hackindia", identity="2026/test", observed=None, **updates):
    from alignn_scraper.models import Observation

    key = {"hackindia": "HackIndia", "luma": "Luma"}[source]
    url = (
        "https://hackindia.org/2026/test" if source == "hackindia" else "https://luma.com/test1234"
    )
    return Observation(
        source=source,
        source_name=key,
        source_id=identity,
        source_url=url,
        apply_url=url,
        observed_at=observed or utcnow(),
        country_evidence={"kind": "country_metadata", "statement": "IN", "url": url},
        title="Python India Hackathon",
        description="Build useful Python applications.",
        organization_name="Published organizer",
        kind="HACKATHON",
        location="Noida, India",
        **updates,
    )


def artifact(*rows):
    from alignn_scraper.bundle import write_bundle
    from alignn_scraper.models import SourceResult

    keys = {r.source for r in rows}
    return write_bundle(
        [
            SourceResult(
                source=k,
                status="ok",
                checked_at=utcnow(),
                records=[r for r in rows if r.source == k],
            )
            for k in keys
        ],
        utcnow(),
    )


def test_import_replay_ordering_and_deadline_version():
    from alignn.domains.opportunities.import_scraped import import_bundle

    now = utcnow()
    first = observation(
        observed=now - timedelta(minutes=2), registration_closes_at=now + timedelta(days=2)
    )
    data = artifact(first)
    assert (
        import_bundle(data, local=True, dry_run=True)["sources"]["hackindia"]["status"] == "VALID"
    )
    with SessionLocal() as db:
        assert db.scalar(select(Opportunity)) is None
    assert import_bundle(data, local=True)["sources"]["hackindia"]["added"] == 1
    assert import_bundle(data, local=True)["sources"]["hackindia"]["status"] == "APPLIED"
    newer = first.model_copy(update={"observed_at": now - timedelta(minutes=1)})
    import_bundle(artifact(newer), local=True)
    with SessionLocal() as db:
        row = db.scalar(select(Opportunity))
        assert row.version == 1 and row.source_imported_at
    extension = newer.model_copy(
        update={"observed_at": now, "registration_closes_at": now + timedelta(days=3)}
    )
    import_bundle(artifact(extension), local=True)
    import_bundle(data, local=True)
    with SessionLocal() as db:
        row = db.scalar(select(Opportunity))
        assert row.version == 2 and row.deadline_version == 2
        assert row.registration_closes_at == extension.registration_closes_at


def test_source_atomicity_and_conflicting_observation():
    from alignn.domains.opportunities.import_scraped import import_bundle

    first = observation()
    import_bundle(artifact(first), local=True)
    conflict = first.model_copy(update={"title": "A conflicting title"})
    reply = import_bundle(artifact(conflict, observation("luma", "evt-123")), local=True)
    assert reply["sources"]["hackindia"]["status"] == "REJECTED"
    assert reply["sources"]["luma"]["status"] == "APPLIED"
    with SessionLocal() as db:
        assert (
            db.scalar(select(Opportunity).where(Opportunity.source_name == "HackIndia")).title
            == first.title
        )


def test_cancel_reopen_and_expiry_keep_saved_records(make_user):
    from alignn.domains.opportunities.import_scraped import import_bundle

    now = utcnow()
    first = observation(observed=now - timedelta(minutes=3))
    import_bundle(artifact(first), local=True)
    user = make_user()
    with SessionLocal.begin() as db:
        row = db.scalar(select(Opportunity))
        identity = row.id
        db.add(SavedOpportunity(user_id=user.id, opportunity_id=identity))
    closed = first.model_copy(
        update={"observed_at": now - timedelta(minutes=2), "source_state": "CANCELLED"}
    )
    import_bundle(artifact(closed), local=True)
    import_bundle(artifact(first), local=True)
    with SessionLocal() as db:
        assert db.get(Opportunity, identity).status == "CLOSED"
    import_bundle(artifact(first.model_copy(update={"observed_at": now})), local=True)
    with SessionLocal() as db:
        assert db.get(Opportunity, identity).status == "PUBLISHED"
        assert db.scalar(select(SavedOpportunity)).opportunity_id == identity


def test_worker_lanes_do_not_lease_slow_collection_in_maintenance():
    from alignn.jobs.worker import enqueue_job, lease_jobs

    now = utcnow()
    with SessionLocal.begin() as db:
        for kind in ["ingest_devfolio", "poll_scraper"]:
            enqueue_job(db, kind=kind, key=kind, payload={}, run_at=now, expires_at=None)
    with SessionLocal.begin() as db:
        leases = lease_jobs(db, worker_id="short", now=now, limit=10, lane="maintenance")
        assert [item.kind for item in leases] == ["poll_scraper"]
    with SessionLocal.begin() as db:
        assert (
            lease_jobs(db, worker_id="long", now=now, limit=10, lane="collection")[0].kind
            == "ingest_devfolio"
        )


def test_recheck_404_needs_spacing_and_new_evidence_wins():
    from alignn.domains.opportunities.recheck import apply_check

    now = utcnow()
    with SessionLocal.begin() as db:
        row = add_opportunity(db)
        row.source_checked_at = now - timedelta(days=1)
        db.flush()
        stamp = row.source_checked_at
        apply_check(db, row.id, stamp, now, status=404)
        assert row.status == "PUBLISHED" and row.missing_count == 1
        apply_check(db, row.id, stamp, now + timedelta(minutes=1), status=404)
        assert row.status == "PUBLISHED"
        apply_check(db, row.id, stamp, now + timedelta(minutes=31), status=404)
        assert row.status == "CLOSED" and row.closure_reason == "source_removed"
        other = add_opportunity(db)
        other.source_checked_at = now
        apply_check(db, other.id, now - timedelta(hours=1), now, status=410)
        assert other.status == "PUBLISHED"
        apply_check(db, other.id, now, now, status=429, error="rate_limited")
        assert other.status == "PUBLISHED" and other.source_error == "rate_limited"


def test_scheduler_registers_models_in_a_clean_process():
    import os
    import subprocess
    import sys

    with SessionLocal.begin() as db:
        add_opportunity(db, ends_at=utcnow() - timedelta(days=1))
    result = subprocess.run(
        [sys.executable, "-c", "from alignn.jobs.scheduler import tick; tick()"],
        env={
            **os.environ,
            "SCRAPER_SYNC_ENABLED": "true",
            "SCRAPER_AUTH_MODE": "cli",
            "SCRAPER_REPOSITORY_ID": "1",
            "SCRAPER_WORKFLOW_ID": "2",
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr[-1200:]


def test_incomplete_ats_recheck_never_closes_another_listing(monkeypatch):
    import json
    import time

    from alignn.domains.opportunities import recheck

    with SessionLocal.begin() as db:
        for identity in ["1", "2"]:
            row = add_opportunity(db)
            row.source_name = "Greenhouse:stripe"
            row.source_id = identity
            row.source_url = f"https://stripe.com/jobs/search?gh_jid={identity}"

    class HTTP:
        def __init__(self, source):
            self.started = time.monotonic()

        def close(self):
            pass

        def get(self, url):
            return json.dumps({"jobs": [], "meta": {"total": 1}})

    monkeypatch.setattr(recheck, "PublicHTTP", HTTP)
    recheck.recheck_source("greenhouse-stripe")
    with SessionLocal() as db:
        assert all(row.status == "PUBLISHED" for row in db.scalars(select(Opportunity)))


def test_closed_saved_history_and_detail_are_readable_only_by_owner(make_user, api_client):
    owner = make_user()
    stranger = make_user()
    with SessionLocal.begin() as db:
        row = add_opportunity(db)
        row.status = "CLOSED"
        identity = row.id
        db.add(SavedOpportunity(user_id=owner.id, opportunity_id=identity))
    client = api_client(owner)
    saved = client.get("/api/v1/me/saved")
    assert saved.status_code == 200 and saved.json()["items"][0]["id"] == str(identity)
    assert client.get(f"/api/v1/opportunities/{identity}").status_code == 200
    assert api_client(stranger).get(f"/api/v1/opportunities/{identity}").status_code in {403, 404}
    assert client.get("/api/v1/opportunities").json()["items"] == []


def test_github_poll_failure_backs_off_new_poll_jobs(monkeypatch):
    from types import SimpleNamespace

    from alignn.domains.opportunities import github_sync

    calls = []

    def fail(settings):
        calls.append(1)
        raise ValueError("github_access_failed")

    monkeypatch.setattr(github_sync, "reader_from_settings", fail)
    settings = SimpleNamespace(scraper_sync_enabled=True)
    try:
        github_sync.poll(settings)
    except ValueError:
        pass
    assert github_sync.poll(settings) == 0
    assert len(calls) == 1


def test_scraper_receipts_and_terminal_jobs_have_bounded_retention():
    from alignn.domains.opportunities.import_scraped import ensure_receipt
    from alignn.jobs.models import Job
    from alignn.jobs.scheduler import prune_scraper_metadata

    now = utcnow()
    with SessionLocal.begin() as db:
        old = ensure_receipt(db, {"local_artifact": "old"}, "hackindia", "a" * 64)
        old.state = "APPLIED"
        old.created_at = now - timedelta(days=31)
        recent = ensure_receipt(db, {"local_artifact": "recent"}, "hackindia", "b" * 64)
        recent.state = "APPLIED"
        recent.created_at = now - timedelta(days=29)
        db.add(
            Job(
                kind="poll_scraper",
                key="old-terminal",
                payload={},
                status="DONE",
                run_at=now - timedelta(days=8),
                created_at=now - timedelta(days=8),
            )
        )
        db.flush()
        assert prune_scraper_metadata(db, now) == 2
        assert db.get(type(recent), recent.id) is not None


def test_artifact_failure_has_a_visible_terminal_receipt(monkeypatch):
    from types import SimpleNamespace

    import pytest

    from alignn.domains.opportunities import github_sync
    from alignn.domains.opportunities.ingestion_models import ImportReceipt
    from alignn.jobs.models import Job

    identity = dict(repository_id=1, workflow_id=2, run_id=3, run_attempt=1, artifact_id=4)
    with SessionLocal.begin() as db:
        db.add(
            Job(
                kind="import_scraper",
                key="scraper-3-1-4",
                payload={},
                status="RUNNING",
                attempts=5,
                run_at=utcnow(),
            )
        )

    class Reader:
        def get(self, path):
            raise ValueError("github_access_failed")

        def close(self):
            pass

    monkeypatch.setattr(github_sync, "reader_from_settings", lambda settings: Reader())
    with pytest.raises(ValueError):
        github_sync.import_artifact(
            SimpleNamespace(), {"identity": identity, "digest": "sha256:" + "a" * 64}
        )
    with SessionLocal() as db:
        receipt = db.scalar(select(ImportReceipt))
        assert receipt and receipt.state == "FAILED" and receipt.error == "artifact_delivery_failed"
