from datetime import timedelta

from sqlalchemy import func, select, update

from alignn.db import SessionLocal, utcnow


def test_rolled_back_signup_has_no_mail_job(db, clock):
    from alignn.jobs.models import Job
    from alignn.jobs.worker import enqueue_job

    enqueue_job(db, kind="mail", key="rollback", payload={}, run_at=clock.now(), expires_at=None)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Job)) == 0


def test_two_workers_do_not_share_a_lease(db):
    from alignn.jobs.worker import enqueue_job, lease_jobs

    enqueue_job(db, kind="mail", key="one", payload={}, run_at=utcnow(), expires_at=None)
    db.commit()
    first = lease_jobs(db, worker_id="first", now=utcnow(), limit=10)
    db.commit()
    with SessionLocal.begin() as other:
        second = lease_jobs(other, worker_id="second", now=utcnow(), limit=10)
    assert len(first) == 1
    assert second == []


def test_expired_lease_can_be_reclaimed(db):
    from alignn.jobs.models import Job
    from alignn.jobs.worker import complete_lease, enqueue_job, lease_jobs

    enqueue_job(db, kind="mail", key="reclaim", payload={}, run_at=utcnow(), expires_at=None)
    db.commit()
    first = lease_jobs(db, worker_id="first", now=utcnow(), limit=1)[0]
    db.commit()
    db.execute(update(Job).values(lease_until=utcnow() - timedelta(seconds=1)))
    db.commit()
    second = lease_jobs(db, worker_id="second", now=utcnow(), limit=1)[0]
    db.commit()
    assert first.lease_token != second.lease_token
    assert complete_lease(db, first) is False
    assert complete_lease(db, second) is True


def test_permanent_failure_is_terminal(db):
    from alignn.jobs.models import Job
    from alignn.jobs.worker import enqueue_job, fail_lease, lease_jobs

    id = enqueue_job(
        db, kind="mail", key="bad-address", payload={}, run_at=utcnow(), expires_at=None
    )
    db.commit()
    lease = lease_jobs(db, worker_id="worker", now=utcnow(), limit=1)[0]
    fail_lease(db, lease, code="invalid_address", permanent=True, now=utcnow())
    db.commit()
    assert db.get(Job, id).status == "FAILED"
    assert lease_jobs(db, worker_id="worker", now=utcnow() + timedelta(days=1), limit=1) == []


def test_retry_exhaustion_is_visible(db):
    from alignn.jobs.models import Job
    from alignn.jobs.worker import enqueue_job, fail_lease, lease_jobs

    id = enqueue_job(db, kind="mail", key="transient", payload={}, run_at=utcnow(), expires_at=None)
    db.commit()
    now = utcnow()
    for attempt in range(5):
        now += timedelta(hours=1)
        lease = lease_jobs(db, worker_id="worker", now=now, limit=1)[0]
        assert lease.attempts == attempt + 1
        fail_lease(db, lease, code="provider_timeout", permanent=False, now=now)
        db.commit()
    assert db.get(Job, id).status == "FAILED"
    assert db.get(Job, id).last_error == "provider_timeout"


def test_job_key_is_unique_and_expires_before_side_effect(db):
    from alignn.jobs.models import Job
    from alignn.jobs.worker import enqueue_job, lease_jobs

    id = enqueue_job(
        db,
        kind="mail",
        key="unique",
        payload={},
        run_at=utcnow(),
        expires_at=utcnow() + timedelta(seconds=1),
    )
    db.commit()
    again = enqueue_job(db, kind="mail", key="unique", payload={}, run_at=utcnow(), expires_at=None)
    assert again == id
    assert lease_jobs(db, worker_id="worker", now=utcnow() + timedelta(seconds=2), limit=1) == []
    assert db.get(Job, id).status == "SKIPPED"


def test_signup_enqueues_verification_mail_without_exposing_token(db):
    from fastapi.testclient import TestClient

    from alignn.jobs.models import Job
    from alignn.main import create_app

    with TestClient(create_app()) as client:
        token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
        result = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "new@alignn.test",
                "full_name": "New Participant",
                "password": "a-long-safe-password42!",
            },
            headers={"origin": "http://localhost:3000", "x-csrf-token": token},
        )
        assert result.status_code == 201
        assert "token" not in result.text
    jobs = db.scalars(select(Job)).all()
    assert len(jobs) == 1
    assert jobs[0].kind == "mail"
    assert jobs[0].payload["to"] == "new@alignn.test"
    assert "/verify-email?token=" in jobs[0].payload["text"]


def test_operator_job_data_is_private(db):
    from fastapi.testclient import TestClient

    from alignn.domains.identity.models import User
    from alignn.domains.identity.service import hasher, issue_session
    from alignn.main import create_app

    with TestClient(create_app()) as client:
        assert client.get("/api/v1/admin/jobs").status_code == 401
        user = User(
            email="member@alignn.test",
            full_name="Member",
            password_hash=hasher.hash("test-password"),
        )
        db.add(user)
        db.flush()
        secret = issue_session(db, user.id, utcnow())
        db.commit()
        client.cookies.set("alignn_session", secret.token)
        assert client.get("/api/v1/admin/jobs").status_code == 403
        user.is_admin = True
        db.commit()
        response = client.get("/api/v1/admin/jobs")
        assert response.status_code == 200
        assert response.json()["items"] == []


def test_replay_requires_a_real_reason_and_records_audit(db):
    from fastapi.testclient import TestClient

    from alignn.audit import AuditRecord
    from alignn.domains.identity.models import User
    from alignn.domains.identity.service import hasher, issue_session
    from alignn.jobs.models import Job
    from alignn.jobs.worker import enqueue_job
    from alignn.main import create_app

    user = User(
        email="operator@alignn.test",
        full_name="Operator",
        is_admin=True,
        password_hash=hasher.hash("local-operator-password"),
    )
    db.add(user)
    db.flush()
    secret = issue_session(db, user.id, utcnow())
    job_id = enqueue_job(
        db,
        kind="mail",
        key="retry-audit",
        payload={"text": "hello"},
        run_at=utcnow(),
        expires_at=None,
    )
    db.flush()
    db.get(Job, job_id).status = "FAILED"
    db.commit()
    with TestClient(create_app()) as client:
        client.cookies.set("alignn_session", secret.token)
        headers = {"origin": "http://localhost:3000", "x-csrf-token": secret.csrf}
        route = f"/api/v1/admin/jobs/{job_id}/replay"
        assert client.post(route, json={"reason": "     "}, headers=headers).status_code == 422
        assert (
            client.post(
                route, json={"reason": "Provider is available again"}, headers=headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                route, json={"reason": "Provider is available again"}, headers=headers
            ).status_code
            == 409
        )
    assert db.scalar(select(func.count()).select_from(AuditRecord)) == 1
