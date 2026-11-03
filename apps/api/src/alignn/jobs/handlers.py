from dataclasses import dataclass

from alignn.adapters.mail import MailAdapter, PermanentDeliveryError
from alignn.config import Settings


@dataclass
class Adapters:
    mail: MailAdapter

    @classmethod
    def configured(cls, settings: Settings):
        return cls(mail=MailAdapter(settings))


def deliver_mail(payload: dict, adapters: Adapters, key: str):
    adapters.mail.send(
        to=payload["to"], subject=payload["subject"], text=payload["text"], delivery_key=key
    )


HANDLERS = {"mail": deliver_mail}


def dispatch(kind: str, payload: dict, adapters: Adapters, key: str):
    handler = HANDLERS.get(kind)
    if not handler:
        raise PermanentDeliveryError("unsupported_job")
    handler(payload, adapters, key)
