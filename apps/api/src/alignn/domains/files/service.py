import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from alignn.domains.files.models import ConsentGrant, PrivateFile
from alignn.domains.identity.schemas import Actor
from alignn.domains.organizations.models import Membership
from alignn.errors import DomainError


@dataclass(frozen=True)
class FileGrant:
    file: PrivateFile
    actor_id: UUID


@dataclass(frozen=True)
class ScanResult:
    clean: bool
    code: str


def authorize_file(
    db: Session, actor: Actor, file_id: UUID, purpose: str = "download"
) -> FileGrant:
    file = db.get(PrivateFile, file_id)
    if not file:
        raise DomainError("not_found", "File not found.", 404)
    if file.owner_id != actor.user_id:
        permission = db.scalar(
            select(ConsentGrant)
            .join(Membership, Membership.organization_id == ConsentGrant.organization_id)
            .where(
                ConsentGrant.file_id == file.id,
                ~ConsentGrant.revoked,
                Membership.user_id == actor.user_id,
                Membership.role.in_(["OWNER", "MANAGER"]),
            )
        )
        if not permission:
            raise DomainError("not_found", "File not found.", 404)
    if file.scan_status != "CLEAN":
        raise DomainError("file_not_ready", "This file has not passed its safety checks.", 409)
    return FileGrant(file, actor.user_id)


def content_type(data: bytes, filename: str) -> str | None:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" and data.startswith(b"%PDF-"):
        return "application/pdf"
    if suffix in {".docx", ".pptx", ".zip"} and zipfile.is_zipfile(io.BytesIO(data)):
        if suffix == ".zip":
            return "application/zip"
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
            required = "word/document.xml" if suffix == ".docx" else "ppt/presentation.xml"
            if "[Content_Types].xml" in names and required in names:
                return (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    if suffix == ".docx"
                    else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
    return None


def verify_upload(db: Session, file_id: UUID, adapters) -> ScanResult:
    file = db.scalar(select(PrivateFile).where(PrivateFile.id == file_id).with_for_update())
    if not file or file.scan_status == "CLEAN":
        return ScanResult(bool(file), "already_processed")
    if file.scan_status not in {"UPLOADED", "SCAN_ERROR"}:
        return ScanResult(False, "not_uploaded")
    with adapters.objects.open(file.object_key) as stream:
        data = stream.read(file.declared_size + 1)
    mime = content_type(data, file.filename)
    if len(data) != file.declared_size or not mime:
        file.scan_status = "REJECTED"
        return ScanResult(False, "file_type_or_size_mismatch")
    # Database row stays locked during the bounded scanner request, preventing replacement races.
    try:
        clean = adapters.scanner.clean(io.BytesIO(data))
    except Exception:
        file.scan_status = "SCAN_ERROR"
        db.flush()
        raise
    file.actual_size = len(data)
    file.sha256 = hashlib.sha256(data).hexdigest()
    file.content_type = mime
    file.scan_status = "CLEAN" if clean else "REJECTED"
    if clean:
        # Presigned upload URLs can be replayed until expiry. Never serve the mutable upload key.
        old_key = file.object_key
        safe_key = f"clean/{uuid4().hex}"
        adapters.objects.put_bytes(safe_key, data, mime)
        file.object_key = safe_key
        from alignn.db import utcnow
        from alignn.jobs.worker import enqueue_job

        enqueue_job(
            db,
            kind="delete_object",
            key=f"delete-upload-{file.id}",
            payload={"object_key": old_key},
            run_at=utcnow(),
            expires_at=None,
        )
    db.flush()
    return ScanResult(clean, "clean" if clean else "malware_detected")
