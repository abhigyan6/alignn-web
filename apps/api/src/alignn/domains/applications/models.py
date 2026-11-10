from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class Application(Record, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "opportunity_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"))
    status: Mapped[str] = mapped_column(String(30), default="SAVED")


class ApplicationEvent(Record, Base):
    __tablename__ = "application_events"
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(2000), default="")
