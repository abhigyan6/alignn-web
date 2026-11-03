from uuid import UUID

from alignn.domains.identity.schemas import StrictModel


class RegistrationCreate(StrictModel):
    team_id: UUID | None = None
    contact_consent: bool = False
    resume_file_id: UUID | None = None


class ConsentUpdate(StrictModel):
    contact: bool
