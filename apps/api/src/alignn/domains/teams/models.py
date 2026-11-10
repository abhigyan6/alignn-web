from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class Team(Record, Base):
    __tablename__ = "teams"
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    captain_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    locked: Mapped[bool] = mapped_column(default=False)


class TeamMember(Record, Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "user_id"),
        UniqueConstraint("team_id", "user_id"),
    )
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"))
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class TeamInvitation(Record, Base):
    __tablename__ = "team_invitations"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    email: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
