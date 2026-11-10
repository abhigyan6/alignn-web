from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Signup(StrictModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)

    @field_validator("full_name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        from email_validator import validate_email

        return validate_email(
            value.strip(), check_deliverability=False, test_environment=True
        ).normalized.lower()


class Login(StrictModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=128)


class EmailRequest(StrictModel):
    email: str = Field(max_length=320)


class TokenRequest(StrictModel):
    token: str = Field(min_length=20, max_length=200)


class ResetRequest(TokenRequest):
    password: str = Field(min_length=12, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    is_admin: bool
    is_verified: bool
    created_at: datetime


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    verified: bool
    admin: bool


@dataclass(frozen=True)
class SessionSecret:
    token: str
    csrf: str
    expires_at: datetime
