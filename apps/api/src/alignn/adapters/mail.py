import smtplib
from email.message import EmailMessage

from alignn.config import Settings


class PermanentDeliveryError(Exception):
    pass


class MailAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, *, to: str, subject: str, text: str, delivery_key: str) -> None:
        if not self.settings.mail_host:
            raise PermanentDeliveryError("mail_not_configured")
        message = EmailMessage()
        message["From"] = self.settings.mail_from
        message["To"] = to
        message["Subject"] = subject
        message["Message-ID"] = f"<{delivery_key}@alignn.test>"
        message.set_content(text)
        try:
            with smtplib.SMTP(self.settings.mail_host, self.settings.mail_port, timeout=10) as smtp:
                if self.settings.environment == "production":
                    import ssl

                    smtp.starttls(context=ssl.create_default_context())
                if self.settings.mail_username and self.settings.mail_password:
                    if self.settings.environment != "production":
                        raise ValueError("SMTP credentials require TLS in production")
                    smtp.login(self.settings.mail_username, self.settings.mail_password.get_secret_value())
                smtp.send_message(message)
        except smtplib.SMTPRecipientsRefused as exc:
            raise PermanentDeliveryError("invalid_address") from exc
