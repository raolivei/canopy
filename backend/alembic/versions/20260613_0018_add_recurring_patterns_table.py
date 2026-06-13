"""Add recurring_patterns table for recurring transaction detection

Revision ID: 20260613_0018
Revises: 20260613_0017
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260613_0018"
down_revision = "20260613_0017"


def upgrade():
    op.create_table(
        "recurring_patterns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("average_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("amount_variance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("next_expected", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("occurrences", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("should_skip_dates", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recurring_patterns_merchant", "recurring_patterns", ["merchant"])
    op.create_index("ix_recurring_patterns_is_active", "recurring_patterns", ["is_active"])
    op.create_index("ix_recurring_patterns_next_expected", "recurring_patterns", ["next_expected"])


def downgrade():
    op.drop_index("ix_recurring_patterns_next_expected", table_name="recurring_patterns")
    op.drop_index("ix_recurring_patterns_is_active", table_name="recurring_patterns")
    op.drop_index("ix_recurring_patterns_merchant", table_name="recurring_patterns")
    op.drop_table("recurring_patterns")
