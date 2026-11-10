from dataclasses import dataclass

from alignn.adapters.mail import MailAdapter, PermanentDeliveryError
from alignn.adapters.objects import configured_objects
from alignn.adapters.scanner import ClamScanner
from alignn.config import Settings


@dataclass
class Adapters:
    mail: MailAdapter
    objects: object = None
    scanner: object = None

    @classmethod
    def configured(cls, settings: Settings):
        return cls(
            mail=MailAdapter(settings),
            objects=configured_objects(settings),
            scanner=ClamScanner(settings.scanner_host, settings.scanner_port),
        )


def deliver_mail(payload: dict, adapters: Adapters, key: str):
    adapters.mail.send(
        to=payload["to"], subject=payload["subject"], text=payload["text"], delivery_key=key
    )


def scan_file(payload: dict, adapters: Adapters, key: str):
    from uuid import UUID

    from alignn.db import SessionLocal
    from alignn.domains.files.models import PrivateFile
    from alignn.domains.files.service import verify_upload

    try:
        with SessionLocal.begin() as db:
            verify_upload(db, UUID(payload["file_id"]), adapters)
    except Exception:
        with SessionLocal.begin() as db:
            file = db.get(PrivateFile, UUID(payload["file_id"]))
            if file and file.scan_status != "CLEAN":
                file.scan_status = "SCAN_ERROR"
        raise


def delete_object(payload: dict, adapters: Adapters, key: str):
    adapters.objects.delete(payload["object_key"])


def rank_profile(payload, adapters, key):
    from uuid import UUID

    from alignn.domains.matching.service import rebuild_matches

    rebuild_matches(UUID(payload["user_id"]))


HANDLERS = {
    "mail": deliver_mail,
    "scan_file": scan_file,
    "delete_object": delete_object,
    "rank_profile": rank_profile,
}


def ingest_remotive(payload, adapters, key):
    from alignn.domains.opportunities.ingestion import sync_remotive
    sync_remotive()


HANDLERS["ingest_remotive"] = ingest_remotive


def dispatch(kind: str, payload: dict, adapters: Adapters, key: str):
    handler = HANDLERS.get(kind)
    if not handler:
        raise PermanentDeliveryError("unsupported_job")
    handler(payload, adapters, key)


def registration_notice(payload, adapters, key):
    from uuid import UUID

    from alignn.db import SessionLocal
    from alignn.domains.identity.models import User

    with SessionLocal() as db:
        user = db.get(User, UUID(payload["user_id"]))
        if not user or not user.is_active:
            return
        email = user.email
    adapters.mail.send(
        to=email,
        subject="Your Alignn registration is confirmed",
        text="You are registered for "
        + payload["title"]
        + ". Open your Alignn workspace for next steps.",
        delivery_key=key,
    )


HANDLERS["registration_notice"] = registration_notice
