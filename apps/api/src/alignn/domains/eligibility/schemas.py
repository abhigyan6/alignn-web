from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator

from alignn.domains.identity.schemas import StrictModel
from alignn.domains.profiles.schemas import BRANCHES, DEGREES


class EligibilityPolicy(StrictModel):
    degree_ids: list[str] = Field(default_factory=list, max_length=20)
    branch_ids: list[str] = Field(default_factory=list, max_length=20)
    graduation_years: list[int] = Field(default_factory=list, max_length=20)
    current_years: list[int] = Field(default_factory=list, max_length=6)
    minimum_cgpa: dict[str, Decimal] = Field(default_factory=dict)

    @field_validator("degree_ids", "branch_ids")
    @classmethod
    def canonical(cls, value, info):
        allowed = DEGREES if info.field_name == "degree_ids" else BRANCHES
        if any(x not in allowed for x in value):
            raise ValueError("Choose canonical degree or branch values")
        return list(dict.fromkeys(value))

    @field_validator("minimum_cgpa")
    @classmethod
    def scales(cls, value):
        if any(k not in {"4", "10"} or v < 0 or v > int(k) for k, v in value.items()):
            raise ValueError("Publish a threshold for each supported 4 or 10 point grading scale")
        return value


class ProfileEvidence(StrictModel):
    verified: bool = False
    degree_id: str | None = None
    branch_id: str | None = None
    graduation_year: int | None = None
    current_year: int | None = None
    cgpa: Decimal | None = None
    cgpa_scale: Literal[4, 10] | None = None


class EligibilityResult(StrictModel):
    status: Literal["ELIGIBLE", "INCOMPLETE", "INELIGIBLE"]
    can_register: bool
    reasons: list[str]
    algorithm_version: str = "eligibility-1"
