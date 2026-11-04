"""Explicit admission snapshot references and registration status constraints."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "3a5803f04b22"
down_revision = "129ba32df140"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "eligibility_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("policy", postgresql.JSONB(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
    )
    op.create_index(
        "ix_eligibility_snapshots_opportunity_id", "eligibility_snapshots", ["opportunity_id"]
    )
    op.add_column("registrations", sa.Column("eligibility_snapshot_id", sa.Uuid(), nullable=True))
    op.execute("UPDATE registrations SET eligibility_snapshot_id = gen_random_uuid()")
    op.execute("""INSERT INTO eligibility_snapshots(id,created_at,opportunity_id,policy_version,policy,evidence)
        SELECT r.eligibility_snapshot_id,r.created_at,r.opportunity_id,r.policy_version,r.policy_snapshot,
        COALESCE((SELECT jsonb_agg(jsonb_build_object('user_id',m.user_id,'profile_revision',m.profile_revision,'evidence',m.admission_evidence) ORDER BY m.user_id)
        FROM registration_members m WHERE m.registration_id=r.id),'[]'::jsonb) FROM registrations r""")
    op.alter_column("registrations", "eligibility_snapshot_id", nullable=False)
    op.create_foreign_key(
        "fk_registration_snapshot",
        "registrations",
        "eligibility_snapshots",
        ["eligibility_snapshot_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_registration_snapshot", "registrations", ["eligibility_snapshot_id"]
    )
    op.create_check_constraint(
        "ck_registration_status",
        "registrations",
        "status IN ('PENDING','CONFIRMED','WITHDRAWN','DISQUALIFIED')",
    )
    op.execute("""UPDATE api_idempotency i SET response=i.response || jsonb_build_object(
        'eligibility_snapshot_id',r.eligibility_snapshot_id,'roster_user_ids',COALESCE(
        (SELECT jsonb_agg(m.user_id ORDER BY m.user_id) FROM registration_members m WHERE m.registration_id=r.id),'[]'::jsonb))
        FROM registrations r WHERE i.operation='register:' || r.opportunity_id::text AND i.response->>'id'=r.id::text""")


def downgrade():
    op.drop_constraint("ck_registration_status", "registrations", type_="check")
    op.drop_constraint("uq_registration_snapshot", "registrations", type_="unique")
    op.drop_constraint("fk_registration_snapshot", "registrations", type_="foreignkey")
    op.drop_column("registrations", "eligibility_snapshot_id")
    op.drop_index("ix_eligibility_snapshots_opportunity_id", table_name="eligibility_snapshots")
    op.drop_table("eligibility_snapshots")
