from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .registry import SOURCES, validate_url


def now_utc():
    return datetime.now(timezone.utc)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(Strict):
    kind: Literal["country_metadata", "official_audience", "official_location"]
    statement: str = Field(min_length=2, max_length=240)
    url: str


class Observation(Strict):
    source: str
    source_name: str
    source_id: str = Field(min_length=1, max_length=180, pattern=r"^[a-zA-Z0-9_:/.-]+$")
    source_url: str
    apply_url: str
    observed_at: datetime
    source_state: Literal["OPEN", "CLOSED", "CANCELLED", "UNKNOWN"] = "OPEN"
    country_code: Literal["IN"] = "IN"
    country_evidence: Evidence
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=20000)
    organization_name: str = Field(min_length=1, max_length=180)
    kind: Literal["HACKATHON", "COMPETITION", "INTERNSHIP", "JOB", "WORKSHOP", "SCHOLARSHIP"]
    location: str = Field(min_length=1, max_length=160)
    work_mode: Literal["REMOTE", "HYBRID", "ONSITE", "UNKNOWN"] = "UNKNOWN"
    registration_closes_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("observed_at", "registration_closes_at", "starts_at", "ends_at")
    @classmethod
    def aware(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("timezone_required")
        return value.astimezone(timezone.utc) if value is not None else None

    @model_validator(mode="after")
    def valid(self):
        if self.source not in SOURCES or self.source_name != SOURCES[self.source].name:
            raise ValueError("source_mismatch")
        validate_url(self.source, self.source_url)
        if self.apply_url != self.source_url or self.country_evidence.url != self.source_url:
            raise ValueError("provenance_mismatch")
        statement = self.country_evidence.statement.casefold()
        if self.country_evidence.kind == "country_metadata":
            if statement not in {"in", "india"}:
                raise ValueError("india_evidence_required")
        elif "india" not in statement:
            raise ValueError("india_evidence_required")
        if self.observed_at > now_utc() + timedelta(minutes=5):
            raise ValueError("future_observation")
        if (
            self.registration_closes_at
            and self.starts_at
            and self.registration_closes_at > self.starts_at
        ):
            raise ValueError("date_order")
        if self.starts_at and self.ends_at and self.starts_at > self.ends_at:
            raise ValueError("date_order")
        return self


class SourceResult(Strict):
    source: str
    status: Literal["ok", "partial", "failed", "empty"]
    checked_at: datetime
    records: list[Observation] = Field(default_factory=list, max_length=100)
    skipped: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def valid(self):
        if self.source not in SOURCES or SOURCES[self.source].status != "enabled":
            raise ValueError("source_not_enabled")
        if self.checked_at.tzinfo is None:
            raise ValueError("timezone_required")
        if len({r.source_id for r in self.records}) != len(self.records):
            raise ValueError("duplicate_identity")
        if any(r.source != self.source or r.observed_at > self.checked_at for r in self.records):
            raise ValueError("source_partition_mismatch")
        if self.status in {"failed", "empty"} and self.records:
            raise ValueError("status_mismatch")
        if self.status == "ok" and not self.records:
            raise ValueError("empty_not_ok")
        if any(not e.replace("_", "").isalnum() or len(e) > 60 for e in self.errors):
            raise ValueError("unsafe_error")
        return self
