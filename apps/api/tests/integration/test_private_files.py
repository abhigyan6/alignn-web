from uuid import UUID

import pytest

from alignn.db import SessionLocal


def init_file(c, **overrides):
    response = c.post(
        "/api/v1/me/files",
        json={"filename": "resume.pdf", "purpose": "resume", "size": 100, **overrides},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_unscanned_file_is_not_downloadable(make_user, api_client):
    c = api_client(make_user(verified=True))
    f = init_file(c)
    response = c.get("/api/v1/me/files/" + f["id"] + "/download")
    assert response.status_code == 409


def test_other_user_cannot_download_private_file(make_user, api_client):
    c = api_client(make_user(verified=True))
    f = init_file(c)
    other = api_client(make_user(verified=True))
    assert other.get("/api/v1/me/files/" + f["id"] + "/download").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"filename": "resume.exe"},
        {"size": 10 * 1024 * 1024 + 1},
        {"purpose": "submission", "filename": "entry.zip", "size": 25 * 1024 * 1024 + 1},
    ],
)
def test_private_file_type_and_size_limits(payload, make_user, api_client):
    c = api_client(make_user(verified=True))
    r = c.post(
        "/api/v1/me/files",
        json={"filename": "resume.pdf", "purpose": "resume", "size": 100, **payload},
    )
    assert r.status_code == 422


def test_failed_scan_stays_private(make_user, api_client):
    from alignn.domains.files.models import PrivateFile

    c = api_client(make_user(verified=True))
    f = init_file(c)
    with SessionLocal.begin() as db:
        db.get(PrivateFile, UUID(f["id"])).scan_status = "REJECTED"
    assert c.get("/api/v1/me/files/" + f["id"] + "/download").status_code == 409


def test_complete_without_uploaded_object_is_a_conflict(make_user, api_client):
    c = api_client(make_user(verified=True))
    f = init_file(c)
    assert c.post("/api/v1/me/files/" + f["id"] + "/complete").status_code == 409


def test_clean_download_uses_immutable_copy(make_user, api_client):
    import io
    from types import SimpleNamespace

    from alignn.adapters.objects import LocalObjects
    from alignn.domains.files.models import PrivateFile
    from alignn.domains.files.service import verify_upload

    payload = b"%PDF-1.7\nA clean test document."
    c = api_client(make_user(verified=True))
    f = init_file(c, size=len(payload))
    assert c.put(f["upload_url"], content=payload).status_code == 200
    objects = LocalObjects()
    with SessionLocal.begin() as db:
        original = db.get(PrivateFile, UUID(f["id"])).object_key
        verdict = verify_upload(
            db,
            UUID(f["id"]),
            SimpleNamespace(
                objects=objects,
                scanner=SimpleNamespace(clean=lambda stream: isinstance(stream, io.BytesIO)),
            ),
        )
        assert verdict.clean
        assert db.get(PrivateFile, UUID(f["id"])).object_key != original
    objects.path(original).write_bytes(b"overwritten quarantine")
    url = c.get("/api/v1/me/files/" + f["id"] + "/download").json()["url"]
    assert c.get(url).content == payload


def test_disguised_pdf_is_rejected_before_scanning(make_user, api_client):
    from types import SimpleNamespace

    from alignn.adapters.objects import LocalObjects
    from alignn.domains.files.service import verify_upload

    payload = b"This is not a PDF."
    c = api_client(make_user(verified=True))
    f = init_file(c, size=len(payload))
    assert c.put(f["upload_url"], content=payload).status_code == 200
    with SessionLocal.begin() as db:
        verdict = verify_upload(
            db, UUID(f["id"]), SimpleNamespace(objects=LocalObjects(), scanner=None)
        )
        assert verdict.clean is False
        assert verdict.code == "file_type_or_size_mismatch"
    assert c.get("/api/v1/me/files/" + f["id"] + "/download").status_code == 409
