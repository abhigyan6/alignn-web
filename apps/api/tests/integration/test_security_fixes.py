from datetime import timedelta

from sqlalchemy import func, select, text

from alignn.config import settings
from alignn.db import SessionLocal, utcnow
from alignn.domains.participation.models import (
    EligibilitySnapshot,
    IdempotencyRecord,
    Registration,
    RegistrationMember,
)
from alignn.jobs.models import Job
from alignn.jobs.retention import prune_retired_event_data


def test_hosting_is_removed_but_external_events_remain(
    make_user, make_organization, make_opportunity, api_client
):
    owner = make_user(verified=True)
    organization = make_organization(owner.id, verified=True)
    legacy = make_opportunity(organization.id, mode="HOSTED", apply_url=None)
    external = make_opportunity(organization.id)
    public = api_client()
    client = api_client(owner)
    assert public.get(f"/api/v1/opportunities/{legacy.id}").status_code == 404
    assert [item["id"] for item in public.get("/api/v1/opportunities").json()["items"]] == [
        str(external.id)
    ]
    assert client.post(f"/api/v1/opportunities/{legacy.id}/teams", json={}).status_code == 404
    assert client.get("/api/v1/me/registrations").status_code == 404
    assert (
        client.post(
            "/api/v1/me/files",
            json={"filename": "project.zip", "purpose": "submission", "size": 10},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/me/files",
            json={"filename": "resume.pdf", "purpose": "resume", "size": 10},
        ).status_code
        == 201
    )


def test_org_identity_changes_revoke_verification_and_invites_are_bounded(
    make_user, make_organization, api_client, monkeypatch
):
    monkeypatch.setattr("alignn.domains.identity.service.utcnow", lambda: now)
    now = utcnow()
    user = make_user(verified=True)
    organization = make_organization(user.id, verified=True)
    client = api_client(user)
    base = f"/api/v1/organizations/{organization.id}"
    for index in range(6):
        response = client.post(
            base + "/invitations", json={"email": f"person{index}@alignn.test", "role": "REVIEWER"}
        )
        assert response.status_code == (201 if index < 5 else 429)
    assert client.patch(base, json={"description": "Updated description"}).json()["verified"]
    assert client.patch(base, json={"name": "New Organization"}).json()["verified"] is False
    assert (
        client.post(
            base + "/invitations", json={"email": "other@alignn.test", "role": "REVIEWER"}
        ).status_code
        == 403
    )
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Job).where(Job.kind == "mail")) == 5


def test_failed_match_job_returns_fallback_and_allows_one_retry(
    make_user, make_organization, make_opportunity, api_client
):
    user = make_user(verified=True)
    org = make_organization(user.id, verified=True)
    make_opportunity(org.id)
    client = api_client(user)
    route = "/api/v1/opportunities?sort=match"
    assert client.get(route).json()["ranking_status"] == "PENDING"
    with SessionLocal.begin() as db:
        job = db.scalar(select(Job).where(Job.kind == "rank_profile"))
        job.status = "FAILED"
        job.run_at = utcnow()
    fallback = client.get(route).json()
    assert fallback["ranking_status"] == "UNAVAILABLE"
    assert fallback["sort"] == "newest" and len(fallback["items"]) == 1
    with SessionLocal.begin() as db:
        db.get(Job, job.id).run_at = utcnow() - timedelta(minutes=6)
    assert client.get(route).json()["ranking_status"] == "PENDING"
    with SessionLocal.begin() as db:
        retry = db.scalar(select(Job).where(Job.key.endswith("-retry")))
        retry.status = "FAILED"
    assert client.get(route).json()["ranking_status"] == "UNAVAILABLE"
    with SessionLocal() as db:
        assert (
            db.scalar(select(func.count()).select_from(Job).where(Job.kind == "rank_profile")) == 2
        )


def test_readiness_requires_current_schema(api_client):
    client = api_client()
    assert client.get("/api/ready").status_code == 200
    with SessionLocal.begin() as db:
        original = db.scalar(text("SELECT version_num FROM alembic_version"))
        db.execute(text("UPDATE alembic_version SET version_num = 'a82d019ef401'"))
    try:
        assert client.get("/api/ready").status_code == 503
    finally:
        with SessionLocal.begin() as db:
            db.execute(
                text("UPDATE alembic_version SET version_num = :revision"), {"revision": original}
            )


def test_retention_expires_replays_and_redacts_old_evidence(
    make_user, make_organization, make_opportunity
):
    user = make_user(verified=True)
    org = make_organization(user.id, verified=True)
    now = utcnow()
    old = now - timedelta(days=settings.retired_event_evidence_retention_days + 1)
    event = make_opportunity(org.id, mode="HOSTED", apply_url=None, ends_at=old)
    with SessionLocal.begin() as db:
        old_snapshot = EligibilitySnapshot(
            opportunity_id=event.id,
            created_at=old,
            policy_version=1,
            policy={},
            evidence=[{"academic": "test"}],
        )
        fresh_snapshot = EligibilitySnapshot(
            opportunity_id=event.id,
            created_at=now,
            policy_version=1,
            policy={},
            evidence=[{"academic": "test"}],
        )
        db.add_all([old_snapshot, fresh_snapshot])
        db.flush()
        registration = Registration(
            opportunity_id=event.id,
            captain_id=user.id,
            eligibility_snapshot_id=old_snapshot.id,
            status="CONFIRMED",
            policy_version=1,
            policy_snapshot={},
        )
        db.add(registration)
        db.flush()
        member = RegistrationMember(
            registration_id=registration.id,
            opportunity_id=event.id,
            user_id=user.id,
            full_name="Participant",
            profile_revision=1,
            admission_evidence={"academic": "test"},
        )
        replay = IdempotencyRecord(
            actor_id=user.id,
            operation="register",
            key="old",
            request_hash="test",
            response={"private": "test"},
            expires_at=old,
        )
        db.add_all([member, replay])
        db.flush()
    with SessionLocal.begin() as db:
        assert prune_retired_event_data(db, now) == 2
    with SessionLocal() as db:
        assert db.get(IdempotencyRecord, replay.id) is None
        assert db.get(EligibilitySnapshot, old_snapshot.id).evidence == []
        assert db.get(EligibilitySnapshot, fresh_snapshot.id).evidence
        assert db.get(RegistrationMember, member.id).admission_evidence == {}
        assert db.get(Registration, registration.id).status == "CONFIRMED"


def test_partial_onboarding_does_not_skip_setup(make_user, api_client):
    user = make_user(verified=True)
    client = api_client(user)
    assert client.get("/api/v1/me/profile").json()["onboarding_complete"] is False
    assert client.post("/api/v1/me/onboarding/complete").status_code == 409
    result = client.put("/api/v1/me/profile", json={"degree_id": "btech", "graduation_year": 2028})
    assert result.status_code == 200, result.text
    assert result.json()["onboarding_complete"] is False
    assert client.post("/api/v1/me/onboarding/complete").status_code == 204
    assert client.get("/api/v1/me/profile").json()["onboarding_complete"] is True
    assert api_client(make_user()).get("/api/v1/me/profile").json()["onboarding_complete"] is False
