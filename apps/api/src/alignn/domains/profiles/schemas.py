from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from alignn.domains.identity.schemas import StrictModel

DEGREES = {"btech", "mtech", "bca", "mca", "bsc", "msc", "bba", "mba", "bcom", "ba", "other"}
BRANCHES = {
    "cse",
    "it",
    "ece",
    "eee",
    "mechanical",
    "civil",
    "design",
    "business",
    "science",
    "other",
}


class ProfileUpdate(StrictModel):
    college: str | None = Field(None, max_length=180)
    degree_id: str | None = None
    branch_id: str | None = None
    graduation_year: int | None = Field(None, ge=2000, le=2100)
    current_year: int | None = Field(None, ge=1, le=6)
    cgpa: Decimal | None = Field(None, ge=0, le=10, decimal_places=2)
    cgpa_scale: Literal[4, 10] | None = None
    location: str | None = Field(None, max_length=160)
    preferred_work_mode: Literal["ANY", "REMOTE", "HYBRID", "ONSITE"] | None = None
    career_interests: list[str] | None = Field(None, max_length=12)
    preferred_locations: list[str] | None = Field(None, max_length=12)
    bio: str | None = Field(None, max_length=1000)
    discoverable: bool | None = None

    @field_validator("degree_id")
    @classmethod
    def degree(cls, value):
        if value is not None and value not in DEGREES:
            raise ValueError("Choose a supported degree")
        return value

    @field_validator("branch_id")
    @classmethod
    def branch(cls, value):
        if value is not None and value not in BRANCHES:
            raise ValueError("Choose a supported branch")
        return value

    @field_validator("career_interests", "preferred_locations")
    @classmethod
    def normalize_tags(cls, value):
        if value is None:
            return None
        normalized = list(dict.fromkeys(v.strip().lower() for v in value if v.strip()))
        if any(len(v) > 80 for v in normalized):
            raise ValueError("Values must be at most 80 characters")
        return normalized

    @model_validator(mode="after")
    def grade(self):
        if self.cgpa is not None and self.cgpa_scale is not None and self.cgpa > self.cgpa_scale:
            raise ValueError("CGPA cannot exceed its grading scale")
        return self


class ProfileOut(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | None = None
    user_id: UUID
    full_name: str
    revision: int
    onboarding_complete: bool


class SkillInput(StrictModel):
    skill_id: str = Field(max_length=60)
    level: Literal["beginner", "intermediate", "advanced"]


class SkillsUpdate(StrictModel):
    skills: list[SkillInput] = Field(max_length=40)

    @model_validator(mode="after")
    def unique(self):
        if len({s.skill_id for s in self.skills}) != len(self.skills):
            raise ValueError("Each skill can appear only once")
        return self


class ProjectCreate(StrictModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(default="", max_length=2000)
    url: str | None = Field(None, max_length=1000)
    skill_ids: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("url")
    @classmethod
    def secure_url(cls, value):
        from urllib.parse import urlsplit

        if value is not None:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("Use a valid HTTPS project link")
        return value


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str
    url: str | None
    skill_ids: list[str]
