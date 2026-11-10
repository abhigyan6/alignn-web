"""Map Clerk subjects without linking accounts by email."""

import sqlalchemy as sa
from alembic import op

revision = "71d2a4b6c801"
down_revision = "3a5803f04b22"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("clerk_subject", sa.String(160), nullable=True))
    op.create_unique_constraint("uq_users_clerk_subject", "users", ["clerk_subject"])
    op.alter_column("users", "password_hash", nullable=True)


def downgrade():
    # Refuse to invent local credentials for Clerk-only accounts.
    op.execute(
        "UPDATE users SET password_hash = '!disabled-clerk-account' WHERE password_hash IS NULL"
    )
    op.alter_column("users", "password_hash", nullable=False)
    op.drop_constraint("uq_users_clerk_subject", "users", type_="unique")
    op.drop_column("users", "clerk_subject")
