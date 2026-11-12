from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import func, select

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.import_scraped import import_bundle
from alignn.domains.opportunities.ingestion_models import ImportReceipt
from alignn.domains.opportunities.models import Opportunity
from alignn.domains.opportunities.visibility import expire_opportunities
from alignn_scraper.bundle import write_bundle
from alignn_scraper.models import Observation, SourceResult


def bundle():
    now = utcnow()
    row = Observation(
        source="hackindia",
        source_name="HackIndia",
        source_id="2026/race",
        source_url="https://hackindia.org/2026/race",
        apply_url="https://hackindia.org/2026/race",
        observed_at=now,
        country_evidence={
            "kind": "country_metadata",
            "statement": "IN",
            "url": "https://hackindia.org/2026/race",
        },
        title="Python Hackathon",
        description="Build useful technology with Python.",
        organization_name="Source",
        kind="HACKATHON",
        location="India",
        registration_closes_at=now + timedelta(days=3),
    )
    return write_bundle(
        [SourceResult(source="hackindia", status="ok", checked_at=now, records=[row])], now
    )


def test_concurrent_replays_commit_once():
    data = bundle()
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: import_bundle(data, local=True), range(2)))
    assert all(r["sources"]["hackindia"]["status"] == "APPLIED" for r in replies)
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Opportunity)) == 1
        assert db.scalar(select(func.count()).select_from(ImportReceipt)) == 1
        assert db.scalar(select(Opportunity)).version == 1


def test_expiry_evaluates_current_deadline_instead_of_stale_job_data():
    import_bundle(bundle(), local=True)
    with SessionLocal.begin() as db:
        row = db.scalar(select(Opportunity))
        assert expire_opportunities(db, utcnow()) == 0
        assert row.status == "PUBLISHED"
