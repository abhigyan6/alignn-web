"""Track onboarding completion separately from partially saved profile fields."""

import sqlalchemy as sa
from alembic import op

revision = "c1595145df22"
down_revision = "a82d019ef401"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    # Preserve workspace access for profiles the old app already considered complete.
    op.execute(
        "UPDATE profiles SET onboarding_completed_at = updated_at "
        "WHERE degree_id IS NOT NULL AND graduation_year IS NOT NULL"
    )


def downgrade():
    op.drop_column("profiles", "onboarding_completed_at")
