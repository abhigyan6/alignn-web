from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr, ValidationError

from alignn.adapters.mail import MailAdapter
from alignn.config import Settings


def test_smtp_authentication_follows_tls():
    settings = Settings.model_construct(
        environment="production", mail_host="smtp.example", mail_port=587,
        mail_from="hello@example.com", mail_username="sender", mail_password=SecretStr("secret"),
    )
    smtp = MagicMock()
    with patch("alignn.adapters.mail.smtplib.SMTP") as factory:
        factory.return_value.__enter__.return_value = smtp
        MailAdapter(settings).send(to="user@example.com", subject="Hello", text="Test", delivery_key="job")
    assert smtp.method_calls[0][0] == "starttls"
    assert smtp.method_calls[1][0] == "login"
    assert smtp.method_calls[2][0] == "send_message"


def test_smtp_credentials_must_be_paired():
    with pytest.raises(ValidationError, match="SMTP username and password"):
        Settings(database_url="postgresql://localhost/alignn", mail_username="sender")
