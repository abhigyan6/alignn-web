from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class Opportunity(Record, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        CheckConstraint("mode IN ('HOSTED','EXTERNAL')"),
        CheckConstraint("capacity > 0 AND capacity_used >= 0 AND capacity_used <= capacity"),
        Index("ix_opportunity_search", "search_vector", postgresql_using="gin"),
        Index("ix_opportunity_public", "status", "registration_closes_at", "id"),
    )
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str]
    organization_name: Mapped[str] = mapped_column(String(180))
    kind: Mapped[str] = mapped_column(String(30))
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    apply_url: Mapped[str | None] = mapped_column(String(1000))
    location: Mapped[str] = mapped_column(String(160), default="Remote")
    work_mode: Mapped[str] = mapped_column(String(20), default="REMOTE")
    registration_closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(default=100)
    capacity_used: Mapped[int] = mapped_column(default=0)
    team_min: Mapped[int] = mapped_column(default=1)
    team_max: Mapped[int] = mapped_column(default=1)
    eligibility: Mapped[dict] = mapped_column(JSONB, default=dict)
    required_skills: Mapped[list] = mapped_column(JSONB, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSONB, default=list)
    interests: Mapped[list] = mapped_column(JSONB, default=list)
    prize: Mapped[str] = mapped_column(String(160), default="")
    version: Mapped[int] = mapped_column(default=1)
    deadline_version: Mapped[int] = mapped_column(default=1)
    admission_started: Mapped[bool] = mapped_column(default=False)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(title,'') || ' ' || coalesce(organization_name,'') || ' ' || coalesce(description,''))",
            persisted=True,
        ),
    )


class SavedOpportunity(Record, Base):
    __tablename__ = "saved_opportunities"
    __table_args__ = (UniqueConstraint("user_id", "opportunity_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))


class MatchSnapshot(Record, Base):
    __tablename__ = "match_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "opportunity_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    profile_revision: Mapped[int]
    opportunity_version: Mapped[int]
    score: Mapped[float]
    evidence: Mapped[dict] = mapped_column(JSONB)
    algorithm_version: Mapped[str] = mapped_column(String(30), default="fit-1")
