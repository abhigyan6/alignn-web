from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select

from alignn.db import utcnow
from alignn.domains.identity.models import LoginSession, User
from alignn.domains.identity.schemas import (
    EmailRequest,
    Login,
    ResetRequest,
    Signup,
    TokenRequest,
    UserOut,
)
from alignn.domains.identity.service import (
    DUMMY_HASH,
    check_csrf,
    consume_action_token,
    digest,
    get_actor,
    hasher,
    issue_action_token,
    issue_session,
    limit,
    load_session,
    revoke_sessions,
    verify_password,
)
from alignn.errors import DomainError
from alignn.jobs.worker import enqueue_job


def local_auth_only(request: Request):
    if request.app.state.settings.auth_provider != "local":
        raise DomainError("managed_auth", "Use Clerk to manage your account.", 410)


router = APIRouter(prefix="/api/v1", tags=["Identity"])
legacy = APIRouter(dependencies=[Depends(local_auth_only)])


def set_session_cookies(request: Request, response: Response, secret) -> None:
    secure = request.app.state.settings.environment == "production"
    max_age = max(0, int((secret.expires_at - utcnow()).total_seconds()))
    response.set_cookie(
        "alignn_session",
        secret.token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        "alignn_csrf",
        secret.csrf,
        httponly=False,
        secure=secure,
        samesite="strict",
        max_age=max_age,
        path="/",
    )


@legacy.get("/auth/csrf")
def csrf(request: Request, response: Response):
    db = request.state.db
    current = load_session(db, request.cookies.get("alignn_session"), utcnow())
    csrf_cookie = request.cookies.get("alignn_csrf", "")
    if current and csrf_cookie and digest(csrf_cookie) == current.csrf_hash:
        return {"csrf_token": csrf_cookie}
    if current:
        import secrets

        csrf_cookie = secrets.token_urlsafe(32)
        current.csrf_hash = digest(csrf_cookie)
        response.set_cookie(
            "alignn_csrf",
            csrf_cookie,
            httponly=False,
            secure=request.app.state.settings.environment == "production",
            samesite="strict",
            path="/",
        )
        return {"csrf_token": csrf_cookie}
    secret = issue_session(db, None, utcnow())
    set_session_cookies(request, response, secret)
    return {"csrf_token": secret.csrf}


@legacy.post(
    "/auth/signup", response_model=UserOut, status_code=201, dependencies=[Depends(check_csrf)]
)
def signup(data: Signup, request: Request):
    db = request.state.db
    limit(db, "signup", request.client.host)
    if db.scalar(select(User).where(User.email == data.email)):
        raise DomainError(
            "signup_unavailable", "Unable to create this account. Try signing in.", 409
        )
    user = User(
        email=data.email, full_name=data.full_name, password_hash=hasher.hash(data.password)
    )
    db.add(user)
    db.flush()
    token = issue_action_token(db, user.id, "verify")
    enqueue_account_mail(db, user, token, "verify", request.app.state.settings.public_origin)
    return user


@legacy.post("/auth/login", response_model=UserOut, dependencies=[Depends(check_csrf)])
def login(data: Login, request: Request, response: Response):
    db = request.state.db
    limit(db, "login-ip", request.client.host)
    email = data.email.strip().lower()
    limit(db, "login-account", email)
    user = db.scalar(select(User).where(User.email == email))
    valid = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise DomainError("invalid_credentials", "Invalid email or password.", 401)
    old_session = load_session(db, request.cookies.get("alignn_session"), utcnow())
    if old_session:
        old_session.revoked = True
    secret = issue_session(db, user.id, utcnow())
    set_session_cookies(request, response, secret)
    return user


@router.get("/me", response_model=UserOut)
def me(request: Request):
    actor = get_actor(request)
    return request.state.db.get(User, actor.user_id)


@legacy.post("/auth/logout", status_code=204, dependencies=[Depends(check_csrf)])
def logout(request: Request, response: Response):
    current = load_session(request.state.db, request.cookies.get("alignn_session"), utcnow())
    if current:
        current.revoked = True
    response.delete_cookie("alignn_session", path="/")
    response.delete_cookie("alignn_csrf", path="/")


@legacy.post("/auth/verify-email", status_code=204, dependencies=[Depends(check_csrf)])
def verify_email(data: TokenRequest, request: Request):
    user = consume_action_token(request.state.db, data.token, "verify")
    user.is_verified = True
    revoke_sessions(request.state.db, user.id)


@legacy.post("/auth/forgot-password", status_code=202, dependencies=[Depends(check_csrf)])
def forgot_password(data: EmailRequest, request: Request):
    db = request.state.db
    limit(db, "reset", request.client.host, 5)
    user = db.scalar(select(User).where(User.email == data.email.strip().lower(), User.is_active))
    if user:
        token = issue_action_token(db, user.id, "reset")
        enqueue_account_mail(db, user, token, "reset", request.app.state.settings.public_origin)
    return {"message": "If the account exists, a reset link will be sent."}


@legacy.post("/auth/reset-password", status_code=204, dependencies=[Depends(check_csrf)])
def reset_password(data: ResetRequest, request: Request):
    user = consume_action_token(request.state.db, data.token, "reset")
    user.password_hash = hasher.hash(data.password)
    revoke_sessions(request.state.db, user.id)


@legacy.get("/me/sessions")
def list_sessions(request: Request):
    actor = get_actor(request)
    rows = request.state.db.scalars(
        select(LoginSession).where(
            LoginSession.user_id == actor.user_id,
            ~LoginSession.revoked,
            LoginSession.expires_at > utcnow(),
        )
    ).all()
    return [
        {
            "id": row.id,
            "created_at": row.created_at,
            "last_seen_at": row.last_seen_at,
            "expires_at": row.expires_at,
        }
        for row in rows
    ]


def enqueue_account_mail(db, user: User, token: str, purpose: str, origin: str):
    from datetime import timedelta

    page = "verify-email" if purpose == "verify" else "reset-password"
    subject = "Verify your Alignn email" if purpose == "verify" else "Reset your Alignn password"
    text = (
        f"{subject}\n\n{origin}/{page}?token={token}\n\n"
        "If you did not request this, you can ignore this message."
    )
    enqueue_job(
        db,
        kind="mail",
        key=f"account-{purpose}-{digest(token)}",
        payload={"to": user.email, "subject": subject, "text": text},
        run_at=utcnow(),
        expires_at=utcnow()
        + (timedelta(hours=24) if purpose == "verify" else timedelta(minutes=30)),
    )


router.include_router(legacy)
