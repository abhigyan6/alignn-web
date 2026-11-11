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
    if key.startswith("organization-invite-"):
        from uuid import UUID

        from alignn.db import SessionLocal, utcnow
        from alignn.domains.organizations.models import Organization, OrganizationInvitation

        with SessionLocal() as db:
            invitation = db.get(
                OrganizationInvitation, UUID(key.removeprefix("organization-invite-"))
            )
            organization = db.get(Organization, invitation.organization_id) if invitation else None
            if (
                not invitation
                or not organization
                or not organization.verified
                or invitation.accepted
                or invitation.expires_at <= utcnow()
                or payload.get("to") != invitation.email
            ):
                return
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


def retire_registration_notice(payload, adapters, key):
    """Drain historical notice jobs without delivering email."""


HANDLERS = {
    "registration_notice": retire_registration_notice,
    "mail": deliver_mail,
    "scan_file": scan_file,
    "delete_object": delete_object,
    "rank_profile": rank_profile,
}


def ingest_remotive(payload, adapters, key):
    from alignn.domains.opportunities.ingestion import sync_remotive

    sync_remotive()


def ingest_devfolio(payload, adapters, key):
    from alignn.config import settings

    if settings.scraper_sync_enabled:
        return
    from alignn.domains.opportunities.devfolio import sync_devfolio

    sync_devfolio()


def ingest_greenhouse(payload, adapters, key):
    from alignn.config import settings

    if settings.scraper_sync_enabled:
        return
    from alignn.domains.opportunities.greenhouse import BOARDS, sync_board

    board = payload.get("board")
    if board not in BOARDS:
        raise PermanentDeliveryError("unsupported_board")
    sync_board(board)


HANDLERS["ingest_greenhouse"] = ingest_greenhouse
HANDLERS["ingest_devfolio"] = ingest_devfolio
HANDLERS["ingest_remotive"] = ingest_remotive


def dispatch(kind: str, payload: dict, adapters: Adapters, key: str):
    handler = HANDLERS.get(kind)
    if not handler:
        raise PermanentDeliveryError("unsupported_job")
    handler(payload, adapters, key)


def poll_scraper(payload, adapters, key):
    from alignn.config import settings
    from alignn.domains.opportunities.github_sync import poll

    if settings.scraper_sync_enabled:
        poll(settings)


def import_scraper(payload, adapters, key):
    from alignn.config import settings
    from alignn.domains.opportunities.github_sync import import_artifact

    if settings.scraper_sync_enabled:
        import_artifact(settings, payload)


def recheck_scraper(payload, adapters, key):
    from alignn.domains.opportunities.recheck import recheck_source

    recheck_source(payload["source"])


HANDLERS.update(
    poll_scraper=poll_scraper, import_scraper=import_scraper, recheck_scraper=recheck_scraper
)
