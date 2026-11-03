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
    tables = [n for n in inspect(engine).get_table_names() if n != "alembic_version"]
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
