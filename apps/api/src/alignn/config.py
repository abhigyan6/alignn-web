from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    public_origin: str = "http://localhost:3000"
    mail_host: str | None = None
    mail_port: int = 1025
    mail_from: str = "hello@alignn.test"
    object_endpoint: str | None = None
    object_bucket: str = "alignn-private"
    object_access_key: str | None = None
    object_secret_key: str | None = None
    scanner_host: str | None = None
    scanner_port: int = 3310

    @model_validator(mode="after")
    def validate_production(self):
        if not self.database_url.startswith("postgresql"):
            raise ValueError("PostgreSQL is required")
        if self.environment == "production":
            if not self.public_origin.startswith("https://"):
                raise ValueError("Production requires an HTTPS public origin")
            if not all(
                (
                    self.mail_host,
                    self.object_endpoint,
                    self.object_access_key,
                    self.object_secret_key,
                    self.scanner_host,
                )
            ):
                raise ValueError(
                    "Production requires mail, private storage and scanner configuration"
                )
        return self


settings = Settings()
