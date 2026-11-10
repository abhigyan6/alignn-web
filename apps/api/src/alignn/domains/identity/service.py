import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from alignn.db import utcnow
from alignn.domains.identity.models import ActionToken, LoginSession, RateLimit, User
from alignn.domains.identity.schemas import Actor, SessionSecret
from alignn.errors import DomainError

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash("timing-only-dummy-password-not-an-account")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def issue_session(db: Session, user_id: UUID | None, now: datetime) -> SessionSecret:
    token, csrf = secrets.token_urlsafe(40), secrets.token_urlsafe(32)
    expires = now + (timedelta(days=7) if user_id else timedelta(minutes=10))
    db.add(
        LoginSession(
            token_hash=digest(token),
            csrf_hash=digest(csrf),
            user_id=user_id,
            expires_at=expires,
            last_seen_at=now,
        )
    )
    db.flush()
    return SessionSecret(token, csrf, expires)


def load_session(db: Session, token: str | None, now: datetime) -> LoginSession | None:
    if not token:
        return None
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == digest(token)))
    if not session or session.revoked or session.expires_at <= now:
        return None
    if session.last_seen_at <= now - timedelta(hours=24):
        return None
    return session


def authenticate_session(db: Session, token: str, now: datetime) -> Actor:
    session = load_session(db, token, now)
    user = db.get(User, session.user_id) if session and session.user_id else None
    if not user or not user.is_active:
        raise DomainError("authentication_required", "Sign in to continue.", 401)
    session.last_seen_at = now
    return Actor(user.id, user.is_verified, user.is_admin)


def get_actor(request: Request) -> Actor:
    if request.app.state.settings.auth_provider == "clerk":
        from alignn.domains.identity.clerk import authenticate_clerk

        return authenticate_clerk(request)
    return authenticate_session(
        request.state.db, request.cookies.get("alignn_session", ""), utcnow()
    )


def require_verified(actor: Actor) -> Actor:
    if not actor.verified:
        raise DomainError("email_verification_required", "Verify your email to continue.", 403)
    return actor


def require_admin(actor: Actor) -> Actor:
    if not actor.admin:
        raise DomainError("forbidden", "You do not have access to this action.", 403)
    return actor


def check_csrf(request: Request) -> None:
    if request.headers.get("origin") != request.app.state.settings.public_origin:
        raise DomainError("invalid_origin", "Reload this page and try again.", 403)
    if request.app.state.settings.auth_provider == "clerk":
        get_actor(request)  # Bearer verification plus exact Origin; never trust legacy cookies.
        return
    session = load_session(request.state.db, request.cookies.get("alignn_session"), utcnow())
    token = request.headers.get("x-csrf-token", "")
    if not session or not token or not secrets.compare_digest(session.csrf_hash, digest(token)):
        raise DomainError("invalid_csrf", "Reload this page and try again.", 403)


def limit(db: Session, scope: str, identity: str, maximum: int = 10) -> None:
    window = int(utcnow().timestamp()) // 60
    statement = insert(RateLimit).values(key=digest(scope + identity), window=window, attempts=1)
    statement = statement.on_conflict_do_update(
        index_elements=[RateLimit.key, RateLimit.window], set_={"attempts": RateLimit.attempts + 1}
    )
    count = db.scalar(statement.returning(RateLimit.attempts))
    if count > maximum:
        raise DomainError("rate_limited", "Too many attempts. Please try again in a minute.", 429)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def issue_action_token(db: Session, user_id: UUID, purpose: str) -> str:
    token = secrets.token_urlsafe(40)
    expires = utcnow() + (timedelta(hours=24) if purpose == "verify" else timedelta(minutes=30))
    db.add(
        ActionToken(user_id=user_id, token_hash=digest(token), purpose=purpose, expires_at=expires)
    )
    db.flush()
    return token


def consume_action_token(db: Session, token: str, purpose: str) -> User:
    row = db.scalar(
        select(ActionToken)
        .where(ActionToken.token_hash == digest(token), ActionToken.purpose == purpose)
        .with_for_update()
    )
    if not row or row.used_at or row.expires_at <= utcnow():
        raise DomainError("invalid_token", "This link has expired or has already been used.")
    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise DomainError("invalid_token", "This link has expired or has already been used.")
    row.used_at = utcnow()
    return user


def revoke_sessions(db: Session, user_id: UUID) -> None:
    db.execute(update(LoginSession).where(LoginSession.user_id == user_id).values(revoked=True))
