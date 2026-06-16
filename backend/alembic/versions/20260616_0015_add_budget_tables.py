"""Add budget tables for tracking spending limits

Revision ID: 20260616_0015
Revises: 20260615_0014
Create Date: 2026-06-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260616_0015'
down_revision = '20260615_0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create budget, budget_categories, and budget_periods tables."""

    # Create budgets table
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),  # 'monthly' or 'yearly'
        sa.Column('user_id', sa.Integer(), nullable=True),  # Future multi-user support
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for budgets
    op.create_index('ix_budgets_user_id', 'budgets', ['user_id'])
    op.create_index('ix_budgets_active', 'budgets', ['active'])

    # Create budget_categories table
    op.create_table(
        'budget_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('budget_id', sa.Integer(), sa.ForeignKey('budgets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_name', sa.String(100), nullable=False),
        sa.Column('amount_limit', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create unique constraint and index for budget_categories
    op.create_unique_constraint('uq_budget_category', 'budget_categories', ['budget_id', 'category_name'])
    op.create_index('ix_budget_categories_budget_id', 'budget_categories', ['budget_id'])

    # Create budget_periods table
    op.create_table(
        'budget_periods',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('budget_id', sa.Integer(), sa.ForeignKey('budgets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('actual_spent', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for budget_periods
    op.create_index('ix_budget_periods_budget_id', 'budget_periods', ['budget_id'])
    op.create_index('ix_budget_periods_dates', 'budget_periods', ['period_start', 'period_end'])


def downgrade() -> None:
    """Drop budget tables."""

    # Drop budget_periods table and indexes
    op.drop_index('ix_budget_periods_dates', table_name='budget_periods')
    op.drop_index('ix_budget_periods_budget_id', table_name='budget_periods')
    op.drop_table('budget_periods')

    # Drop budget_categories table and indexes
    op.drop_index('ix_budget_categories_budget_id', table_name='budget_categories')
    op.drop_constraint('uq_budget_category', 'budget_categories', type_='unique')
    op.drop_table('budget_categories')

    # Drop budgets table and indexes
    op.drop_index('ix_budgets_active', table_name='budgets')
    op.drop_index('ix_budgets_user_id', table_name='budgets')
    op.drop_table('budgets')
