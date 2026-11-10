"""Exercise actual RSA verification and the PostgreSQL identity boundary offline."""

import time
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import select

from alignn.config import Settings
from alignn.db import SessionLocal, utcnow
from alignn.domains.identity import clerk
from alignn.domains.identity.models import User
from alignn.domains.identity.service import issue_session
from alignn.main import create_app


@pytest.fixture
def clerk_client(monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    config = Settings(
        auth_provider="clerk", clerk_secret_key="sk_test_fixture", clerk_jwt_key=public
    )
    subject = "user_" + uuid4().hex
    remote = {
        "id": subject,
        "first_name": "Alignn",
        "last_name": "Student",
        "primary_email_address_id": "email_test",
        "email_addresses": [
            {
                "id": "email_test",
                "email_address": f"{subject}@alignn.test",
                "verification": {"status": "verified"},
            }
        ],
        "public_metadata": {"is_admin": True},
    }
    monkeypatch.setattr(clerk, "fetch_clerk_user", lambda *_: remote)

    def token(**overrides):
        now = int(time.time())
        claims = {
            "sub": subject,
            "sid": "sess_fixture",
            "iss": "https://fixture.clerk.accounts.dev",
            "iat": now,
            "nbf": now - 1,
            "exp": now + 60,
            "azp": "http://localhost:3000",
            "v": 2,
            "is_admin": True,
        }
        claims.update(overrides)
        return jwt.encode(claims, private, algorithm="RS256")

    with TestClient(create_app(config)) as client:
        client.headers.update(
            {"authorization": "Bearer " + token(), "origin": config.public_origin}
        )
        yield client, token, remote


def test_clerk_provisions_once_without_browser_roles(clerk_client):
    client, _, remote = clerk_client
    first = client.get("/api/v1/me")
    assert first.status_code == 200, first.text
    assert first.json()["is_verified"] and not first.json()["is_admin"]
    assert client.get("/api/v1/me").json()["id"] == first.json()["id"]
    assert client.put("/api/v1/me/profile", json={"degree_id": "btech"}).status_code == 200
    remote["email_addresses"][0]["verification"]["status"] = "unverified"
    assert not client.get("/api/v1/me").json()["is_verified"]
    with SessionLocal() as db:
        assert len(db.scalars(select(User)).all()) == 1
        assert db.scalar(select(User)).password_hash is None


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": 1},
        {"nbf": 4102444800},
        {"azp": "https://evil.example"},
        {"exp": None},
        {"sid": None},
        {"sts": "pending"},
        {"sub": "admin"},
    ],
)
def test_clerk_rejects_invalid_session_claims(clerk_client, claims):
    client, token, _ = clerk_client
    client.headers["authorization"] = "Bearer " + token(**claims)
    assert client.get("/api/v1/me").status_code == 401


def test_clerk_rejects_wrong_signature_and_machine_tokens(clerk_client):
    client, _, _ = clerk_client
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    for token in [
        jwt.encode({"sub": "user_fake", "exp": int(time.time()) + 60}, other, algorithm="RS256"),
        "ak_fake",
        "m2m_fake",
        "not-a-token",
    ]:
        client.headers["authorization"] = "Bearer " + token
        assert client.get("/api/v1/me").status_code == 401


def test_clerk_never_links_by_email(clerk_client, make_user):
    client, _, remote = clerk_client
    existing = make_user(email=remote["email_addresses"][0]["email_address"])
    response = client.get("/api/v1/me")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "account_migration_required"
    with SessionLocal() as db:
        assert db.get(User, existing.id).clerk_subject is None


def test_clerk_disabled_accounts_and_deleted_remote_users_fail_closed(clerk_client):
    client, _, remote = clerk_client
    response = client.get("/api/v1/me")
    with SessionLocal.begin() as db:
        from uuid import UUID

        db.get(User, UUID(response.json()["id"])).is_active = False
    assert client.get("/api/v1/me").status_code == 401
    remote["banned"] = True
    assert client.get("/api/v1/me").status_code == 401


def test_clerk_disables_legacy_auth_and_cookies(clerk_client, make_user):
    client, _, _ = clerk_client
    client.headers.pop("authorization")
    with SessionLocal.begin() as db:
        secret = issue_session(db, make_user().id, utcnow())
    client.cookies.set("alignn_session", secret.token)
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/opportunities").status_code == 200
    for path in ["/auth/login", "/auth/signup", "/auth/logout", "/auth/reset-password"]:
        assert client.post("/api/v1" + path, json={}).status_code == 410
    assert client.get("/api/v1/me/sessions").status_code == 410


def test_clerk_mutations_reject_wrong_origin(clerk_client):
    client, _, _ = clerk_client
    client.headers["origin"] = "https://evil.example"
    assert client.put("/api/v1/me/profile", json={"degree_id": "btech"}).status_code == 403
