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
