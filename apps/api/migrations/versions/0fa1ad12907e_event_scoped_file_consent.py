"""event_scoped_file_consent"""

import sqlalchemy as sa
from alembic import op

revision = "0fa1ad12907e"
down_revision = "5f03da3a8231"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("file_consent_grants", sa.Column("opportunity_id", sa.Uuid(), nullable=False))
    op.drop_constraint(op.f("uq_file_organization_grant"), "file_consent_grants", type_="unique")
    op.create_unique_constraint(
        "uq_file_event_grant", "file_consent_grants", ["file_id", "opportunity_id"]
    )
    op.create_foreign_key(
        "fk_consent_opportunity",
        "file_consent_grants",
        "opportunities",
        ["opportunity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column("file_download_tickets", sa.Column("opportunity_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_ticket_opportunity",
        "file_download_tickets",
        "opportunities",
        ["opportunity_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_ticket_opportunity", "file_download_tickets", type_="foreignkey")
    op.drop_column("file_download_tickets", "opportunity_id")
    op.drop_constraint("fk_consent_opportunity", "file_consent_grants", type_="foreignkey")
    op.drop_constraint("uq_file_event_grant", "file_consent_grants", type_="unique")
    op.create_unique_constraint(
        op.f("uq_file_organization_grant"),
        "file_consent_grants",
        ["file_id", "organization_id"],
        postgresql_nulls_not_distinct=False,
    )
    op.drop_column("file_consent_grants", "opportunity_id")
