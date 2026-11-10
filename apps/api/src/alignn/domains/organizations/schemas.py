from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from alignn.domains.identity.schemas import StrictModel


class OrganizationCreate(StrictModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = Field(default="", max_length=3000)
    website: str | None = Field(None, max_length=1000)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("website")
    @classmethod
    def https(cls, value):
        from urllib.parse import urlsplit

        if value is not None:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("Use a valid HTTPS website")
        return value


class OrganizationUpdate(StrictModel):
    name: str | None = Field(None, min_length=2, max_length=180)
    description: str | None = Field(None, max_length=3000)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return OrganizationCreate.trim_name(value)


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str
    website: str | None
    verified: bool


class InvitationCreate(StrictModel):
    email: str = Field(max_length=320)
    role: Literal["MANAGER", "REVIEWER"]

    @field_validator("email")
    @classmethod
    def email_value(cls, value):
        from email_validator import validate_email

        return validate_email(
            value.strip(), check_deliverability=False, test_environment=True
        ).normalized.lower()


class OwnershipTransfer(StrictModel):
    user_id: UUID
