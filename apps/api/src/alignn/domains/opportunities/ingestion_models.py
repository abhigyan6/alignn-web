"""Durable source receipts; collector artifacts contain no user data."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from alignn.db import Base, Record


class ImportReceipt(Record, Base):
    __tablename__ = "scraper_import_receipts"
    __table_args__ = (
        CheckConstraint(
            "state IN ('DISCOVERED','IMPORTING','APPLIED','REJECTED','RETRYABLE','FAILED')"
        ),
    )
    identity_key: Mapped[str] = mapped_column(String(64), unique=True)
    identity: Mapped[dict] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(60))
    digest: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), default="DISCOVERED", index=True)
    counts: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(String(80))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ScraperCursor(Record, Base):
    __tablename__ = "scraper_cursors"
    key: Mapped[str] = mapped_column(String(120), unique=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)
