"""Clerk authenticates identity; PostgreSQL remains the authorization authority."""

import httpx
from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from email_validator import EmailNotValidError, validate_email
from fastapi import Request
from sqlalchemy import select, text

from alignn.domains.identity.models import User
from alignn.domains.identity.schemas import Actor
from alignn.errors import DomainError


def verify_clerk_request(request: Request) -> str:
    config = request.app.state.settings
    if not config.clerk_secret_key:
        raise DomainError("auth_unconfigured", "Sign-in is not configured yet.", 503)
    # Only explicitly supplied session tokens are accepted, never legacy cookies or API keys.
    if not request.headers.get("authorization", "").startswith("Bearer "):
        raise DomainError("authentication_required", "Sign in to continue.", 401)
    try:
        state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=config.clerk_secret_key.get_secret_value(),
                jwt_key=config.clerk_jwt_key,
                authorized_parties=[config.public_origin],
                accepts_token=["session_token"],
            ),
        )
    except Exception:
        # Do not log SDK exceptions: they may contain credentials or token material.
        raise DomainError("authentication_unavailable", "Sign-in is temporarily unavailable.", 503)
    if not state.is_signed_in or not state.payload:
        raise DomainError("authentication_required", "Sign in again to continue.", 401)
    if (
        not isinstance(state.payload.get("exp"), (int, float))
        or not isinstance(state.payload.get("nbf"), (int, float))
        or not isinstance(state.payload.get("sid"), str)
        or state.payload.get("sts") == "pending"
    ):
        raise DomainError("authentication_required", "Complete sign-in to continue.", 401)
    subject = state.payload.get("sub")
    if not isinstance(subject, str) or not subject.startswith("user_") or len(subject) > 160:
        raise DomainError("authentication_required", "Sign in again to continue.", 401)
    return subject


def fetch_clerk_user(secret_key: str, subject: str) -> dict:
    try:
        response = httpx.get(
            f"https://api.clerk.com/v1/users/{subject}",
            headers={"Authorization": f"Bearer {secret_key}"},
            timeout=10,
        )
        if response.status_code == 404:
            raise DomainError("authentication_required", "Sign in again to continue.", 401)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        raise DomainError("authentication_unavailable", "Sign-in is temporarily unavailable.", 503)


def authenticate_clerk(request: Request) -> Actor:
    if hasattr(request.state, "clerk_actor"):
        return request.state.clerk_actor
    subject = verify_clerk_request(request)
    remote = fetch_clerk_user(
        request.app.state.settings.clerk_secret_key.get_secret_value(), subject
    )
    if remote.get("id") != subject or remote.get("banned") or remote.get("locked"):
        raise DomainError("authentication_required", "Sign in again to continue.", 401)
    primary = next(
        (
            e
            for e in remote.get("email_addresses", [])
            if e.get("id") == remote.get("primary_email_address_id")
        ),
        None,
    )
    if not primary:
        raise DomainError("email_required", "Add an email address to your Clerk account.", 403)
    try:
        email = validate_email(
            primary["email_address"],
            check_deliverability=False,
            test_environment=request.app.state.settings.environment != "production",
        ).normalized.lower()
    except (EmailNotValidError, KeyError):
        raise DomainError("email_required", "Add a valid email to your Clerk account.", 403)
    verified = (primary.get("verification") or {}).get("status") == "verified"
    full_name = (
        " ".join(str(remote.get(k) or "").strip() for k in ("first_name", "last_name")).strip()
        or email.split("@")[0]
    )
    db = request.state.db
    # Serializes first-use provisioning for this identity, including parallel /me + saves calls.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:subject, 0))"), {"subject": subject}
    )
    user = db.scalar(select(User).where(User.clerk_subject == subject))
    conflict = db.scalar(select(User).where(User.email == email))
    if conflict and (not user or conflict.id != user.id):
        raise DomainError(
            "account_migration_required",
            "An existing Alignn account uses this email. Contact support to migrate it safely.",
            409,
        )
    if user and not user.is_active:
        raise DomainError("authentication_required", "This account is unavailable.", 401)
    if not user:
        user = User(
            clerk_subject=subject,
            email=email,
            full_name=full_name[:160],
            password_hash=None,
            is_verified=verified,
            is_admin=False,
        )
        db.add(user)
    else:
        user.email, user.full_name, user.is_verified = email, full_name[:160], verified
    db.flush()
    actor = Actor(user.id, verified, user.is_admin)
    request.state.clerk_actor = actor
    return actor
