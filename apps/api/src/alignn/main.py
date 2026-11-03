import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alignn.config import Settings
from alignn.config import settings as default_settings
from alignn.db import SessionLocal
from alignn.domains.identity.router import router as identity_router
from alignn.errors import DomainError

logger = logging.getLogger("alignn")


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or default_settings
    app = FastAPI(
        title="Alignn API",
        version="0.1.0",
        docs_url=None if config.environment == "production" else "/docs",
    )
    app.state.settings = config

    @app.middleware("http")
    async def transactions(request: Request, call_next):
        request.state.request_id = str(uuid4())
        with SessionLocal() as db:
            request.state.db = db
            try:
                response = await call_next(request)
                if response.status_code < 400 or response.status_code in {401, 429}:
                    # Failed sign-in attempts must persist their rate-limit counters.
                    db.commit()
                else:
                    db.rollback()
            except IntegrityError:
                db.rollback()
                response = JSONResponse(
                    status_code=409,
                    content={
                        "error": {
                            "code": "conflict",
                            "message": "This action conflicts with an existing record.",
                            "request_id": request.state.request_id,
                        }
                    },
                )
            except Exception:
                db.rollback()
                logger.exception("Request failed", extra={"request_id": request.state.request_id})
                response = JSONResponse(
                    status_code=500,
                    content={
                        "error": {
                            "code": "internal_error",
                            "message": "Something went wrong. Please try again.",
                            "request_id": request.state.request_id,
                        }
                    },
                )
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": request.state.request_id,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]} for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_input",
                    "message": "Check the highlighted fields.",
                    "fields": fields,
                    "request_id": request.state.request_id,
                }
            },
        )

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "service": "Alignn"}

    @app.get("/api/ready")
    def ready(request: Request):
        try:
            request.state.db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            return {"status": "ready"}
        except Exception:
            return JSONResponse(status_code=503, content={"status": "unavailable"})

    app.include_router(identity_router)
    return app


app = create_app()
