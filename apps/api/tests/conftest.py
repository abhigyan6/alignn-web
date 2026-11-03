import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

config = dotenv_values(Path(__file__).resolve().parents[3] / ".env")
test_url = os.environ.get("TEST_DATABASE_URL") or config.get("TEST_DATABASE_URL")
if not test_url or "test" not in test_url.rsplit("/", 1)[-1]:
    raise RuntimeError("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database")
os.environ["DATABASE_URL"] = test_url
os.environ["ENVIRONMENT"] = "test"

from sqlalchemy import inspect, text  # noqa: E402

from alignn.db import engine  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    tables = [
        n for n in inspect(engine).get_table_names() if n not in {"alembic_version", "skills"}
    ]
    if tables:
        names = ", ".join('"' + t.replace('"', '""') + '"' for t in tables)
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {names} CASCADE"))
    yield


@pytest.fixture
def db():
    from alignn.db import SessionLocal

    with SessionLocal() as session:
        yield session
        session.rollback()


@pytest.fixture
def clock():
    from datetime import datetime, timezone

    class Clock:
        def now(self):
            return datetime.now(timezone.utc)

    return Clock()


@pytest.fixture
def make_user():
    from uuid import uuid4

    from alignn.db import SessionLocal
    from alignn.domains.identity.models import User
    from alignn.domains.identity.service import hasher

    def create(verified=False, admin=False, email=None):
        with SessionLocal.begin() as db:
            user = User(
                email=email or f"{uuid4().hex}@alignn.test",
                full_name="Test Participant",
                password_hash=hasher.hash("Test-password-42!"),
                is_verified=verified,
                is_admin=admin,
            )
            db.add(user)
            db.flush()
            return user

    return create


@pytest.fixture
def api_client():
    from contextlib import ExitStack

    from fastapi.testclient import TestClient

    from alignn.db import SessionLocal, utcnow
    from alignn.domains.identity.service import issue_session
    from alignn.main import create_app

    app = create_app()
    app.openapi()
    with ExitStack() as stack:

        def create(user=None):
            client = stack.enter_context(TestClient(app))
            if user:
                with SessionLocal.begin() as db:
                    secret = issue_session(db, user.id, utcnow())
                client.cookies.set("alignn_session", secret.token)
                client.cookies.set("alignn_csrf", secret.csrf)
                client.headers.update(
                    {"origin": "http://localhost:3000", "x-csrf-token": secret.csrf}
                )
            return client

        yield create


@pytest.fixture
def make_organization():
    from alignn.db import SessionLocal
    from alignn.domains.organizations.models import Membership, Organization

    def create(owner_id, verified=False):
        with SessionLocal.begin() as db:
            o = Organization(name="Test Builders", verified=verified)
            db.add(o)
            db.flush()
            db.add(Membership(organization_id=o.id, user_id=owner_id, role="OWNER"))
            return o

    return create


@pytest.fixture
def make_opportunity():
    from datetime import timedelta

    from alignn.db import SessionLocal, utcnow
    from alignn.domains.opportunities.models import Opportunity

    def create(organization_id, **overrides):
        values = dict(
            organization_id=organization_id,
            organization_name="Test Builders",
            title="Build tomorrow",
            description="A student event for meaningful projects",
            kind="HACKATHON",
            mode="HOSTED",
            status="PUBLISHED",
            registration_closes_at=utcnow() + timedelta(days=10),
            starts_at=utcnow() + timedelta(days=11),
            ends_at=utcnow() + timedelta(days=12),
        )
        values.update(overrides)
        with SessionLocal.begin() as db:
            o = Opportunity(**values)
            db.add(o)
            db.flush()
            return o

    return create
