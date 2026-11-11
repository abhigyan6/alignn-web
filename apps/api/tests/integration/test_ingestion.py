import httpx
import pytest
from sqlalchemy import select

from alignn.db import SessionLocal
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


def test_retired_source_never_imports():
    with client([listing()]) as http:
        assert sync_remotive(http)["status"] == "retired"
    with SessionLocal() as db:
        assert db.scalar(select(Opportunity)) is None
