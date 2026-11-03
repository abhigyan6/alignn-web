import hashlib
import secrets
from datetime import timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from alignn.adapters.objects import LocalObjects, configured_objects
from alignn.db import utcnow
from alignn.domains.files.models import ConsentGrant, DownloadTicket, PrivateFile
from alignn.domains.files.schemas import FileInit, GrantCreate
from alignn.domains.files.service import authorize_file
from alignn.domains.identity.service import check_csrf, digest, get_actor, limit
from alignn.domains.opportunities.service import visible
from alignn.errors import DomainError
from alignn.jobs.worker import enqueue_job

router = APIRouter(prefix="/api/v1", tags=["Private files"])


@router.get("/me/files")
def my_files(request: Request):
    actor = get_actor(request)
    rows = request.state.db.scalars(
        select(PrivateFile)
        .where(PrivateFile.owner_id == actor.user_id)
        .order_by(PrivateFile.created_at.desc())
        .limit(100)
    ).all()
    return {
        "items": [
            {
                "id": f.id,
                "filename": f.filename,
                "purpose": f.purpose,
                "scan_status": f.scan_status,
                "size": f.actual_size or f.declared_size,
                "created_at": f.created_at,
            }
            for f in rows
        ]
    }


@router.post("/me/files", status_code=201, dependencies=[Depends(check_csrf)])
def initialize(data: FileInit, request: Request):
    actor = get_actor(request)
    db = request.state.db
    limit(db, "upload", str(actor.user_id), 10)
    token = secrets.token_urlsafe(40)
    file = PrivateFile(
        owner_id=actor.user_id,
        filename=data.filename,
        purpose=data.purpose,
        declared_size=data.size,
        object_key=f"quarantine/{uuid4().hex}",
        upload_token_hash=digest(token),
        upload_expires_at=utcnow() + timedelta(minutes=5),
    )
    db.add(file)
    db.flush()
    objects = configured_objects(request.app.state.settings)
    if isinstance(objects, LocalObjects):
        url = f"/api/v1/me/files/{file.id}/upload?token={token}"
    else:
        url = objects.upload_url(file.object_key, file.declared_size)
    return {
        "id": file.id,
        "upload_url": url,
        "expires_at": file.upload_expires_at,
        "method": "PUT",
        "complete_required": not isinstance(objects, LocalObjects),
    }


def owned_pending(request, id):
    actor = get_actor(request)
    file = request.state.db.scalar(
        select(PrivateFile)
        .where(PrivateFile.id == id, PrivateFile.owner_id == actor.user_id)
        .with_for_update()
    )
    if not file:
        raise DomainError("not_found", "File not found.", 404)
    if file.scan_status != "PENDING":
        raise DomainError("already_uploaded", "This upload has already been used.", 409)
    if file.upload_expires_at <= utcnow():
        raise DomainError("upload_expired", "Start a new upload.", 409)
    return file


@router.put("/me/files/{id}/upload", dependencies=[Depends(check_csrf)])
async def upload(id: UUID, request: Request, token: str = Query(max_length=200)):
    file = owned_pending(request, id)
    objects = configured_objects(request.app.state.settings)
    if not isinstance(objects, LocalObjects):
        raise DomainError("direct_upload_required", "Use the signed storage upload URL.", 409)
    if not secrets.compare_digest(file.upload_token_hash, digest(token)):
        raise DomainError("invalid_upload", "This upload link is invalid.", 403)
    target = objects.path(file.object_key)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    size = 0
    checksum = hashlib.sha256()
    try:
        with target.open("xb") as output:
            import os

            os.fchmod(output.fileno(), 0o600)
            async for chunk in request.stream():
                size += len(chunk)
                if size > file.declared_size or file.upload_expires_at <= utcnow():
                    raise DomainError(
                        "invalid_upload_size", "The upload exceeded its size or time limit.", 422
                    )
                checksum.update(chunk)
                await run_in_threadpool(output.write, chunk)
        if size != file.declared_size:
            raise DomainError(
                "invalid_upload_size", "The uploaded size does not match the file.", 422
            )
    except Exception:
        target.unlink(missing_ok=True)
        raise
    file.actual_size = size
    file.sha256 = checksum.hexdigest()
    mark_uploaded(request, file)
    return {"id": file.id, "scan_status": file.scan_status}


def mark_uploaded(request, file):
    file.scan_status = "UPLOADED"
    enqueue_job(
        request.state.db,
        kind="scan_file",
        key=f"scan-{file.id}",
        payload={"file_id": str(file.id)},
        run_at=utcnow(),
        expires_at=utcnow() + timedelta(days=1),
    )


@router.post("/me/files/{id}/complete", dependencies=[Depends(check_csrf)])
def complete_upload(id: UUID, request: Request):
    file = owned_pending(request, id)
    objects = configured_objects(request.app.state.settings)
    try:
        size = objects.size(file.object_key)
    except FileNotFoundError:
        raise DomainError("upload_missing", "Upload the file before completing it.", 409)
    if size != file.declared_size:
        raise DomainError("invalid_upload_size", "The uploaded size does not match the file.", 422)
    mark_uploaded(request, file)
    return {"id": file.id, "scan_status": file.scan_status}


@router.get("/me/files/{id}/download")
def download(id: UUID, request: Request, opportunity_id: UUID | None = None):
    actor = get_actor(request)
    file = authorize_file(request.state.db, actor, id, opportunity_id=opportunity_id).file
    objects = configured_objects(request.app.state.settings)
    if not isinstance(objects, LocalObjects):
        return {"url": objects.download_url(file.object_key, file.filename), "expires_in": 300}
    token = secrets.token_urlsafe(40)
    request.state.db.add(
        DownloadTicket(
            file_id=id,
            opportunity_id=opportunity_id,
            actor_id=actor.user_id,
            token_hash=digest(token),
            expires_at=utcnow() + timedelta(minutes=5),
        )
    )
    return {"url": f"/api/v1/files/{id}/content?ticket={token}", "expires_in": 300}


@router.get("/files/{id}/content")
def content(id: UUID, request: Request, ticket: str = Query(max_length=200)):
    actor = get_actor(request)
    grant = request.state.db.scalar(
        select(DownloadTicket).where(
            DownloadTicket.file_id == id,
            DownloadTicket.actor_id == actor.user_id,
            DownloadTicket.token_hash == digest(ticket),
            DownloadTicket.expires_at > utcnow(),
        )
    )
    if not grant:
        raise DomainError("not_found", "This download link is no longer available.", 404)
    file = authorize_file(request.state.db, actor, id, opportunity_id=grant.opportunity_id).file
    objects = configured_objects(request.app.state.settings)
    if not isinstance(objects, LocalObjects):
        raise DomainError("not_found", "Use the private storage download link.", 404)
    return FileResponse(
        objects.path(file.object_key),
        filename=file.filename,
        media_type="application/octet-stream",
        content_disposition_type="attachment",
    )


@router.post("/me/files/{id}/grants", dependencies=[Depends(check_csrf)])
def grant_consent(id: UUID, data: GrantCreate, request: Request):
    actor = get_actor(request)
    db = request.state.db
    file = db.get(PrivateFile, id)
    if not file or file.owner_id != actor.user_id:
        raise DomainError("not_found", "File not found.", 404)
    opportunity = visible(db, actor, data.opportunity_id)
    if file.purpose != "resume":
        raise DomainError(
            "invalid_grant", "Only a resume can be shared through this consent flow.", 422
        )
    grant = db.scalar(
        select(ConsentGrant).where(
            ConsentGrant.file_id == id, ConsentGrant.opportunity_id == data.opportunity_id
        )
    )
    if grant:
        grant.revoked = False
    else:
        grant = ConsentGrant(
            file_id=id,
            opportunity_id=opportunity.id,
            owner_id=actor.user_id,
            organization_id=opportunity.organization_id,
        )
        db.add(grant)
        db.flush()
    return {"id": grant.id, "opportunity_id": grant.opportunity_id, "revoked": False}


@router.delete("/me/file-grants/{id}", status_code=204, dependencies=[Depends(check_csrf)])
def revoke_consent(id: UUID, request: Request):
    actor = get_actor(request)
    grant = request.state.db.scalar(
        select(ConsentGrant).where(ConsentGrant.id == id, ConsentGrant.owner_id == actor.user_id)
    )
    if not grant:
        raise DomainError("not_found", "Consent grant not found.", 404)
    grant.revoked = True
