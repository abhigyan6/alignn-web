from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from alignn.db import SessionLocal, utcnow
from alignn.domains.opportunities.models import Opportunity, SavedOpportunity
from alignn.domains.opportunities.schemas import SearchQuery
from alignn.domains.opportunities.service import search_opportunities
from alignn.domains.organizations.models import Organization


def add_opportunity(db, **kwargs):
    org = Organization(name='Source', verified=False)
    db.add(org)
    db.flush()
    row = Opportunity(organization_id=org.id, title='Build useful technology',
                      description='A public Indian student hackathon.', organization_name='Source',
                      kind='HACKATHON', mode='EXTERNAL', status='PUBLISHED',
                      apply_url='https://hackindia.org/2026/test', source_name='HackIndia',
                      source_id=uuid4().hex, **kwargs)
    db.add(row)
    db.flush()
    return row


def test_discovery_hides_ended_and_retired_but_keeps_ongoing():
    with SessionLocal.begin() as db:
        ended = add_opportunity(db, ends_at=utcnow()-timedelta(seconds=1))
        live = add_opportunity(db, starts_at=utcnow()-timedelta(days=1),
                               ends_at=utcnow()+timedelta(days=1))
        retired = add_opportunity(db)
        retired.source_name = 'Remotive'
        found = search_opportunities(db, None, SearchQuery())['items']
        assert [item.id for item in found] == [live.id]
        assert db.get(Opportunity, ended.id) is not None


def test_retirement_and_expiry_preserve_saved_history(make_user):
    from alignn.domains.opportunities.visibility import expire_opportunities
    user = make_user()
    with SessionLocal.begin() as db:
        row = add_opportunity(db)
        row.source_name = 'Remotive'
        db.add(SavedOpportunity(user_id=user.id, opportunity_id=row.id))
        ended = add_opportunity(db, ends_at=utcnow()-timedelta(days=1))
        assert expire_opportunities(db, utcnow()) == 2
        assert row.status == ended.status == 'CLOSED'
        assert db.scalar(select(SavedOpportunity)).opportunity_id == row.id
        assert expire_opportunities(db, utcnow()) == 0


def test_remotive_jobs_never_fetch_and_are_not_scheduled(monkeypatch):
    from alignn.domains.opportunities.ingestion import schedule_ingestion, sync_remotive
    from alignn.jobs.handlers import dispatch
    from alignn.jobs.models import Job
    import httpx
    monkeypatch.setattr(httpx.Client, 'stream', lambda *a, **k: (_ for _ in ()).throw(
        AssertionError('Retired source must not fetch')))
    assert sync_remotive()['status'] == 'retired'
    dispatch('ingest_remotive', {}, None, 'old-job')
    with SessionLocal.begin() as db:
        schedule_ingestion(db, utcnow())
        assert not db.scalar(select(Job).where(Job.kind == 'ingest_remotive'))
