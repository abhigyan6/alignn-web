from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from alignn.domains.identity.schemas import StrictModel


class RegistrationCreate(StrictModel):
    team_id: UUID | None = None
    contact_consent: bool = False
    resume_file_id: UUID | None = None


class ConsentUpdate(StrictModel):
    contact: bool


class RosterMemberOut(BaseModel):
    user_id: UUID
    full_name: str
    profile_revision: int


class RegistrationOut(BaseModel):
    id: UUID
    opportunity_id: UUID
    team_id: UUID | None
    eligibility_snapshot_id: UUID
    captain_id: UUID
    status: Literal["PENDING", "CONFIRMED", "WITHDRAWN", "DISQUALIFIED"]
    roster_user_ids: list[UUID]
    roster: list[RosterMemberOut]
    policy_version: int
    created_at: datetime
    request_id: str
