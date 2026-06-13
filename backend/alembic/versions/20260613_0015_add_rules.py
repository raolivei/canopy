"""Add transaction rules engine tables

Revision ID: 20260613_0015
Revises: 20260612_0014
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260613_0015"
down_revision = "20260612_0014"


def upgrade():
    # Rules table
    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rules_active_priority", "rules", ["is_active", "priority"])
    op.create_index("ix_rules_created_at", "rules", ["created_at"])

    # Rule conditions table
    op.create_table(
        "rule_conditions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field", sa.String(50), nullable=False),  # enum: merchant, amount, description, category, account, original_statement, tags
        sa.Column("operator", sa.String(50), nullable=False),  # enum: equals, contains, regex, starts_with, ends_with, greater_than, less_than, greater_equal, less_equal
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("numeric_value", sa.Numeric(precision=18, scale=2), nullable=True),
    )
    op.create_index("ix_rule_conditions_rule_id", "rule_conditions", ["rule_id"])

    # Rule actions table
    op.create_table(
        "rule_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),  # enum: set_category, add_tag, split
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("split_config", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_rule_actions_rule_id", "rule_actions", ["rule_id"])


def downgrade():
    op.drop_index("ix_rule_actions_rule_id")
    op.drop_table("rule_actions")
    op.drop_index("ix_rule_conditions_rule_id")
    op.drop_table("rule_conditions")
    op.drop_index("ix_rules_created_at")
    op.drop_index("ix_rules_active_priority")
    op.drop_table("rules")
