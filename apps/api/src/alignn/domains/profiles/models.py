from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record, utcnow


class Profile(Record, Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("cgpa IS NULL OR (cgpa >= 0 AND cgpa <= cgpa_scale)"),
        CheckConstraint("cgpa_scale IS NULL OR cgpa_scale IN (4,10)"),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    college: Mapped[str | None] = mapped_column(String(180))
    degree_id: Mapped[str | None] = mapped_column(String(40))
    branch_id: Mapped[str | None] = mapped_column(String(40))
    graduation_year: Mapped[int | None]
    current_year: Mapped[int | None]
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    cgpa_scale: Mapped[int | None]
    location: Mapped[str | None] = mapped_column(String(160))
    preferred_work_mode: Mapped[str] = mapped_column(String(20), default="ANY")
    career_interests: Mapped[list] = mapped_column(JSONB, default=list)
    preferred_locations: Mapped[list] = mapped_column(JSONB, default=list)
    bio: Mapped[str | None] = mapped_column(String(1000))
    discoverable: Mapped[bool] = mapped_column(default=False)
    revision: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Skill(Record, Base):
    __tablename__ = "skills"
    key: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    aliases: Mapped[list] = mapped_column(JSONB, default=list)
    category: Mapped[str] = mapped_column(String(40))


class ProfileSkill(Record, Base):
    __tablename__ = "profile_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_profile_skill"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id"))
    level: Mapped[str] = mapped_column(String(20))


class Project(Record, Base):
    __tablename__ = "projects"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(String(2000), default="")
    url: Mapped[str | None] = mapped_column(String(1000))
    skill_ids: Mapped[list] = mapped_column(JSONB, default=list)
