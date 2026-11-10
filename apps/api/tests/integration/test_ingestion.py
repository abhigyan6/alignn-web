from datetime import timedelta

import httpx
import pytest
from sqlalchemy import select

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.ingestion import normalize, sync_remotive
from alignn.domains.opportunities.models import Opportunity


def listing(id=123):
    return dict(
        id=id,
        url=f"https://remotive.com/remote-jobs/software-dev/example-{id}",
        title="Python internship",
        company_name="Example",
        description="<p>Build Python applications.</p><script>unsafe()</script>",
        job_type="internship",
    )


def client(rows):
    return httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"jobs": rows, "job-count": len(rows)})
        )
    )


def test_normalize_does_not_invent_dates_or_eligibility():
    row = normalize(listing())
    assert row["kind"] == "INTERNSHIP"
    assert "unsafe" not in row["description"]
    assert "<p>" not in row["description"]
    assert "registration_closes_at" not in row
    with pytest.raises(ValueError):
        normalize({**listing(), "url": "https://example.com/wrong"})


def test_sync_deduplicates_throttles_updates_and_closes():
    with client([listing()]) as http:
        assert sync_remotive(http)["imported"] == 1
        assert sync_remotive(http)["status"] == "throttled"
    with SessionLocal.begin() as db:
        first = db.scalar(select(Opportunity))
        identity = first.id
        first.source_checked_at = utcnow() - timedelta(hours=7)
        assert first.registration_closes_at is None
        assert first.status == "PUBLISHED"
    with client([{**listing(), "title": "Updated Python internship"}]) as http:
        sync_remotive(http)
    with SessionLocal.begin() as db:
        first = db.get(Opportunity, identity)
        assert first.title == "Updated Python internship"
        assert first.version == 2
        first.source_checked_at = utcnow() - timedelta(hours=7)
    with client([listing(456)]) as http:
        sync_remotive(http)
    with SessionLocal() as db:
        assert db.get(Opportunity, identity).status == "CLOSED"
        assert len(db.scalars(select(Opportunity)).all()) == 2


def test_bad_snapshot_does_not_replace_catalog():
    with client([listing()]) as http:
        sync_remotive(http)
    with SessionLocal.begin() as db:
        db.scalar(select(Opportunity)).source_checked_at = utcnow() - timedelta(hours=7)
    with client([]) as http, pytest.raises(ValueError):
        sync_remotive(http)
    with SessionLocal() as db:
        assert db.scalar(select(Opportunity)).status == "PUBLISHED"
