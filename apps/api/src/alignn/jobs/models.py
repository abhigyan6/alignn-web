from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class Job(Record, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_dispatch", "status", "run_at"),
        CheckConstraint("attempts >= 0 AND attempts <= 5"),
    )
    kind: Mapped[str] = mapped_column(String(50))
    key: Mapped[str] = mapped_column(String(255), unique=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), default="QUEUED")
    attempts: Mapped[int] = mapped_column(default=0)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[UUID | None]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[str | None] = mapped_column(String(100))
    last_error: Mapped[str | None] = mapped_column(String(100))
