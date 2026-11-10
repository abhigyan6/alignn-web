from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from alignn.main import create_app

ORIGIN = "http://localhost:3000"
USER = {"email": "test@alignn.test", "password": "Long-valid-password42!", "full_name": "Test User"}


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def csrf(client):
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    return {"origin": ORIGIN, "x-csrf-token": response.json()["csrf_token"]}


def signup(client):
    response = client.post("/api/v1/auth/signup", json=USER, headers=csrf(client))
    assert response.status_code == 201, response.text
    return response.json()


def login(client):
    response = client.post(
        "/api/v1/auth/login", json={k: USER[k] for k in ("email", "password")}, headers=csrf(client)
    )
    assert response.status_code == 200, response.text
    return response


def test_public_signup_cannot_create_admin(client):
    response = client.post(
        "/api/v1/auth/signup", json={**USER, "role": "ADMIN"}, headers=csrf(client)
    )
    assert response.status_code == 422


def test_signup_login_and_cookie_session(client):
    data = signup(client)
    assert data["email"] == USER["email"]
    assert data["is_admin"] is False
    response = login(client)
    assert "access_token" not in response.json()
    assert "HttpOnly" in response.headers.get("set-cookie", "")
    assert client.get("/api/v1/me").json()["id"] == data["id"]


def test_logout_revokes_session(client):
    signup(client)
    login(client)
    old_token = client.cookies.get("alignn_session")
    assert client.post("/api/v1/auth/logout", headers=csrf(client)).status_code == 204
    client.cookies.set("alignn_session", old_token)
    assert client.get("/api/v1/me").status_code == 401


def test_cross_origin_mutation_rejected(client):
    headers = csrf(client)
    headers["origin"] = "https://evil.example"
    assert client.post("/api/v1/auth/signup", json=USER, headers=headers).status_code == 403


def test_mutation_without_csrf_rejected(client):
    assert (
        client.post("/api/v1/auth/signup", json=USER, headers={"origin": ORIGIN}).status_code == 403
    )


def test_session_absolute_and_idle_expiry(client):
    from sqlalchemy import update

    from alignn.db import SessionLocal
    from alignn.domains.identity.models import LoginSession

    signup(client)
    login(client)
    with SessionLocal.begin() as db:
        db.execute(
            update(LoginSession).values(
                last_seen_at=datetime.now(timezone.utc) - timedelta(hours=25)
            )
        )
    assert client.get("/api/v1/me").status_code == 401
    login(client)
    with SessionLocal.begin() as db:
        db.execute(
            update(LoginSession).values(
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)
            )
        )
    assert client.get("/api/v1/me").status_code == 401


def test_disabled_user_session_rejected(client):
    from sqlalchemy import update

    from alignn.db import SessionLocal
    from alignn.domains.identity.models import User

    signup(client)
    login(client)
    with SessionLocal.begin() as db:
        db.execute(update(User).values(is_active=False))
    assert client.get("/api/v1/me").status_code == 401


def test_password_reset_single_use(client):
    from uuid import UUID

    from alignn.db import SessionLocal
    from alignn.domains.identity.service import issue_action_token

    user = signup(client)
    with SessionLocal.begin() as db:
        token = issue_action_token(db, UUID(user["id"]), "reset")
    payload = {"token": token, "password": "A-new-strong-password42!"}
    assert (
        client.post("/api/v1/auth/reset-password", json=payload, headers=csrf(client)).status_code
        == 204
    )
    assert (
        client.post("/api/v1/auth/reset-password", json=payload, headers=csrf(client)).status_code
        == 400
    )


def test_wrong_password_returns_generic_error(client):
    signup(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": USER["email"], "password": "wrong"},
        headers=csrf(client),
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_password_whitespace_is_not_silently_changed(client):
    password = "  a-valid-password-with-spaces  "
    created = client.post(
        "/api/v1/auth/signup", json={**USER, "password": password}, headers=csrf(client)
    )
    assert created.status_code == 201
    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": USER["email"], "password": password.strip()},
        headers=csrf(client),
    )
    assert wrong.status_code == 401
    correct = client.post(
        "/api/v1/auth/login",
        json={"email": USER["email"], "password": password},
        headers=csrf(client),
    )
    assert correct.status_code == 200
