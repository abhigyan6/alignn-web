"""External opportunity provenance and unknown source dates."""

import sqlalchemy as sa
from alembic import op

revision = "a82d019ef401"
down_revision = "71d2a4b6c801"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("registration_closes_at", "starts_at", "ends_at"):
        op.alter_column("opportunities", name, nullable=True)
    for name, size in (("source_name", 60), ("source_id", 180), ("source_url", 1000)):
        op.add_column("opportunities", sa.Column(name, sa.String(size), nullable=True))
    op.add_column("opportunities", sa.Column("source_checked_at", sa.DateTime(timezone=True)))
    op.create_unique_constraint(
        "uq_opportunity_source", "opportunities", ["source_name", "source_id"]
    )


def downgrade():
    # Existing external records with unknown dates must be explicitly handled before rollback.
    for name in ("registration_closes_at", "starts_at", "ends_at"):
        op.alter_column("opportunities", name, nullable=False)
    op.drop_constraint("uq_opportunity_source", "opportunities", type_="unique")
    for name in ("source_name", "source_id", "source_url", "source_checked_at"):
        op.drop_column("opportunities", name)
