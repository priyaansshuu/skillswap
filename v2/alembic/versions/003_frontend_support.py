"""Add member skill suggestions and request submission idempotency."""

import sqlalchemy as sa

from alembic import op

revision = "003_frontend"
down_revision = "002_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "request_submissions",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(36), sa.ForeignKey("requests.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "skill_suggestions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("explanation", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("skill_id", sa.String(36), sa.ForeignKey("skills.id")),
        sa.Column("resolution", sa.String(1000)),
        sa.Column("decision", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name="suggestion_status"),
    )
    op.create_index("ix_suggestions_user_created", "skill_suggestions", ["user_id", "created_at"])


def downgrade():
    op.drop_table("skill_suggestions")
    op.drop_table("request_submissions")
