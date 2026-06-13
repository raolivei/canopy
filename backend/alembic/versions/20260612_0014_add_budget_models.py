"""Add budget models - Budget, BudgetCategory, and BudgetTracking

Revision ID: 20260612_0014
Revises: 20260501_0013
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260612_0014"
down_revision = "20260501_0013"


def upgrade():
    # Create budgets table
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="CAD"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_budgets_is_active", "budgets", ["is_active"])
    op.create_index("ix_budgets_created_at", "budgets", ["created_at"])

    # Create budget_categories table
    op.create_table(
        "budget_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("budget_id", sa.Integer(), nullable=False),
        sa.Column("category_name", sa.String(100), nullable=False),
        sa.Column("limit_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("period_type", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("rollover_excess", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_budget_categories_budget_id", "budget_categories", ["budget_id"])
    op.create_index("ix_budget_categories_category_name", "budget_categories", ["category_name"])
    op.create_index("ix_budget_categories_period_type", "budget_categories", ["period_type"])

    # Create budget_tracking table for audit/history
    op.create_table(
        "budget_tracking",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("budget_id", sa.Integer(), nullable=False),
        sa.Column("budget_category_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_spent", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("actual_spent_updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("rollover_amount", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["budget_category_id"], ["budget_categories.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_budget_tracking_budget_id", "budget_tracking", ["budget_id"])
    op.create_index("ix_budget_tracking_period", "budget_tracking", ["period_start", "period_end"])
    op.create_index("ix_budget_tracking_category", "budget_tracking", ["budget_category_id"])


def downgrade():
    op.drop_index("ix_budget_tracking_category")
    op.drop_index("ix_budget_tracking_period")
    op.drop_index("ix_budget_tracking_budget_id")
    op.drop_table("budget_tracking")

    op.drop_index("ix_budget_categories_period_type")
    op.drop_index("ix_budget_categories_category_name")
    op.drop_index("ix_budget_categories_budget_id")
    op.drop_table("budget_categories")

    op.drop_index("ix_budgets_created_at")
    op.drop_index("ix_budgets_is_active")
    op.drop_table("budgets")
