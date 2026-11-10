from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator

from alignn.domains.eligibility.schemas import EligibilityPolicy
from alignn.domains.identity.schemas import StrictModel
from alignn.domains.profiles.schemas import ProjectCreate


class OpportunityCreate(StrictModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=20000)
    kind: Literal["HACKATHON", "COMPETITION", "INTERNSHIP", "JOB", "WORKSHOP", "SCHOLARSHIP"]
    mode: Literal["EXTERNAL"] = "EXTERNAL"
    apply_url: str = Field(max_length=1000)
    location: str = Field("Remote", max_length=160)
    work_mode: Literal["REMOTE", "HYBRID", "ONSITE"] = "REMOTE"
    registration_closes_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    eligibility: EligibilityPolicy = Field(default_factory=EligibilityPolicy)
    required_skills: list[str] = Field(default_factory=list, max_length=40)
    preferred_skills: list[str] = Field(default_factory=list, max_length=40)
    interests: list[str] = Field(default_factory=list, max_length=12)
    prize: str = Field("", max_length=160)

    @field_validator("apply_url")
    @classmethod
    def url(cls, v):
        return ProjectCreate.secure_url(v)

    @field_validator("registration_closes_at", "starts_at", "ends_at")
    @classmethod
    def timezone(cls, v):
        if v is not None and v.tzinfo is None:
            raise ValueError("Include a timezone")
        return v

    @model_validator(mode="after")
    def valid(self):
        if (
            self.registration_closes_at
            and self.starts_at
            and self.registration_closes_at > self.starts_at
        ) or (self.starts_at and self.ends_at and self.starts_at > self.ends_at):
            raise ValueError("Registration, start and end must be in order")
        return self


class OpportunityOut(OpportunityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    organization_name: str
    status: str
    version: int
    deadline_version: int
    created_at: datetime
    source_name: str | None = None
    source_url: str | None = None
    source_checked_at: datetime | None = None


class VersionCommand(StrictModel):
    expected_version: int = Field(ge=1)


class OpportunityMutation(VersionCommand):
    opportunity: OpportunityCreate


class SearchQuery(StrictModel):
    q: str = Field("", max_length=200)
    kind: str | None = None
    mode: Literal["EXTERNAL"] | None = None
    sort: Literal["deadline", "newest", "match"] = "deadline"
    limit: int = Field(20, ge=1, le=100)
    cursor: int = Field(0, ge=0, le=1000000)
