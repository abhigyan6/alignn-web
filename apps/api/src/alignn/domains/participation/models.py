from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class Registration(Record, Base):
    __tablename__ = "registrations"
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    captain_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    team_id: Mapped[UUID | None] = mapped_column(ForeignKey("teams.id"))
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','CONFIRMED','WITHDRAWN','DISQUALIFIED')",
            name="ck_registration_status",
        ),
    )
    eligibility_snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("eligibility_snapshots.id"), unique=True
    )
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    policy_version: Mapped[int]
    policy_snapshot: Mapped[dict] = mapped_column(JSONB)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RegistrationMember(Record, Base):
    __tablename__ = "registration_members"
    __table_args__ = (
        UniqueConstraint("registration_id", "user_id"),
        Index(
            "uq_active_event_participant",
            "opportunity_id",
            "user_id",
            unique=True,
            postgresql_where=text("active"),
        ),
    )
    registration_id: Mapped[UUID] = mapped_column(ForeignKey("registrations.id"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    active: Mapped[bool] = mapped_column(default=True)
    full_name: Mapped[str] = mapped_column(String(160))
    profile_revision: Mapped[int]
    admission_evidence: Mapped[dict] = mapped_column(JSONB)


class IdempotencyRecord(Record, Base):
    __tablename__ = "api_idempotency"
    __table_args__ = (UniqueConstraint("actor_id", "operation", "key"),)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    operation: Mapped[str] = mapped_column(String(120))
    key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class EventConsent(Record, Base):
    __tablename__ = "event_consents"
    __table_args__ = (UniqueConstraint("user_id", "opportunity_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"))
    contact: Mapped[bool] = mapped_column(default=False)


class EligibilitySnapshot(Record, Base):
    __tablename__ = "eligibility_snapshots"
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    policy_version: Mapped[int]
    policy: Mapped[dict] = mapped_column(JSONB)
    evidence: Mapped[list] = mapped_column(JSONB)
