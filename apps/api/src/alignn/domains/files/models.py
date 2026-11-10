from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class PrivateFile(Record, Base):
    __tablename__ = "private_files"
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(180))
    purpose: Mapped[str] = mapped_column(String(20))
    object_key: Mapped[str] = mapped_column(String(200), unique=True)
    declared_size: Mapped[int]
    actual_size: Mapped[int | None]
    sha256: Mapped[str | None] = mapped_column(String(64))
    content_type: Mapped[str | None] = mapped_column(String(160))
    scan_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    upload_token_hash: Mapped[str] = mapped_column(String(64))
    upload_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConsentGrant(Record, Base):
    __tablename__ = "file_consent_grants"
    __table_args__ = (UniqueConstraint("file_id", "opportunity_id", name="uq_file_event_grant"),)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    file_id: Mapped[UUID] = mapped_column(ForeignKey("private_files.id", ondelete="CASCADE"))
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    revoked: Mapped[bool] = mapped_column(default=False)


class DownloadTicket(Record, Base):
    __tablename__ = "file_download_tickets"
    file_id: Mapped[UUID] = mapped_column(ForeignKey("private_files.id", ondelete="CASCADE"))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    opportunity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE")
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
