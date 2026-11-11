from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

# Source checkouts use the monorepo root; container/wheel installations can have
# fewer ancestors and receive their production settings through the environment.
ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "apps/api/pyproject.toml").is_file()),
    Path.cwd(),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", ROOT / "apps/web/.env.local"), extra="ignore"
    )
    environment: Literal["development", "test", "production"] = "development"
    auth_provider: Literal["local", "clerk"] = "clerk"
    clerk_secret_key: SecretStr | None = None
    clerk_jwt_key: str | None = None
    database_url: str
    retired_event_evidence_retention_days: int = Field(default=180, ge=30)
    database_pool_size: int = Field(default=3, ge=1, le=100)
    database_max_overflow: int = Field(default=2, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=1, le=120)
    public_origin: str = "http://localhost:3000"
    mail_host: str | None = None
    mail_port: int = 1025
    mail_from: str = "hello@alignn.test"
    mail_username: str | None = None
    mail_password: SecretStr | None = None
    object_endpoint: str | None = None
    object_driver: Literal["local", "s3"] = "local"
    object_auth_mode: Literal["static", "iam"] = "static"
    object_region: str | None = None
    object_bucket: str = "alignn-private"
    object_access_key: str | None = None
    object_secret_key: SecretStr | None = None
    scanner_host: str | None = None
    scanner_port: int = 3310

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Heroku supplies postgres://; select our installed psycopg 3 driver explicitly.
        url = make_url(value)
        if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
            raise ValueError("PostgreSQL with psycopg is required")
        return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)

    @model_validator(mode="after")
    def validate_production(self):
        if bool(self.mail_username) != bool(self.mail_password):
            raise ValueError("SMTP username and password must be configured together")
        if not self.database_url.startswith("postgresql"):
            raise ValueError("PostgreSQL is required")
        if self.object_auth_mode == "iam":
            if self.object_driver != "s3" or not self.object_region:
                raise ValueError("IAM object storage requires S3 and an explicit AWS region")
            if self.object_endpoint or self.object_access_key or self.object_secret_key:
                raise ValueError(
                    "IAM object storage uses native AWS endpoints and role credentials"
                )
        if self.environment == "production":
            if self.auth_provider == "clerk" and not self.clerk_secret_key:
                raise ValueError("Clerk authentication requires a secret key")
            if self.object_driver != "s3":
                raise ValueError("Production requires private S3-compatible storage")
            if not self.public_origin.startswith("https://"):
                raise ValueError("Production requires an HTTPS public origin")
            if not all(
                (
                    self.mail_host,
                    self.object_auth_mode == "iam"
                    or all((self.object_endpoint, self.object_access_key, self.object_secret_key)),
                    self.scanner_host,
                )
            ):
                raise ValueError(
                    "Production requires mail, private storage and scanner configuration"
                )
        return self


settings = Settings()
