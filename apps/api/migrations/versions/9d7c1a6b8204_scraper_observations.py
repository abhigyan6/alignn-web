"""Source observations, bounded inventory and atomic import receipts."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "9d7c1a6b8204"
down_revision = "c1595145df22"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("source_imported_at", "next_check_at", "last_attempt_at", "missing_since"):
        op.add_column("opportunities", sa.Column(name, sa.DateTime(timezone=True)))
    for name, size in [
        ("source_content_hash", 64),
        ("source_state", 16),
        ("closure_reason", 60),
        ("source_error", 60),
    ]:
        op.add_column("opportunities", sa.Column(name, sa.String(size)))
    op.add_column("opportunities", sa.Column("country_evidence", postgresql.JSONB()))
    op.add_column(
        "opportunities",
        sa.Column("missing_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_opportunities_next_check_at", "opportunities", ["next_check_at"])
    op.create_table(
        "scraper_import_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("identity_key", sa.String(64), nullable=False, unique=True),
        sa.Column("identity", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(60), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("counts", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.String(80)),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "state IN ('DISCOVERED','IMPORTING','APPLIED','REJECTED','RETRYABLE','FAILED')"
        ),
    )
    op.create_index("ix_scraper_import_receipts_state", "scraper_import_receipts", ["state"])
    op.create_table(
        "scraper_cursors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("key", sa.String(120), nullable=False, unique=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
    )
    op.execute(
        "UPDATE opportunities SET status='CLOSED', closure_reason='source_retired', version=version+1 WHERE source_name='Remotive' AND status='PUBLISHED'"
    )


def downgrade():
    op.drop_table("scraper_cursors")
    op.drop_table("scraper_import_receipts")
    op.drop_index("ix_opportunities_next_check_at", table_name="opportunities")
    for name in (
        "source_imported_at",
        "next_check_at",
        "last_attempt_at",
        "missing_since",
        "source_content_hash",
        "source_state",
        "closure_reason",
        "source_error",
        "country_evidence",
        "missing_count",
    ):
        op.drop_column("opportunities", name)
