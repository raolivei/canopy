"""Add financial_profiles table for Growth Advisor

Revision ID: 20260219_0004
Revises: 20260201_0003
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20260219_0004'
down_revision = '20260201_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'financial_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        # Location & immigration
        sa.Column('country_of_residence', sa.String(length=2), nullable=False, server_default='CA'),
        sa.Column('province_or_state', sa.String(length=10), nullable=True),
        sa.Column('citizenship', sa.String(length=2), nullable=True),
        sa.Column('visa_type', sa.String(length=30), nullable=True, server_default='citizen'),
        # Income
        sa.Column('annual_gross_income', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0'),
        sa.Column('income_currency', sa.String(length=10), nullable=False, server_default='CAD'),
        sa.Column('employment_type', sa.String(length=30), nullable=False, server_default='employee'),
        # Cash flow
        sa.Column('monthly_expenses', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0'),
        sa.Column('monthly_savings', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0'),
        # Goals
        sa.Column('goals', JSONB, nullable=True),
        # Planning horizon
        sa.Column('target_retirement_age', sa.Integer(), nullable=True),
        sa.Column('current_age', sa.Integer(), nullable=True),
        sa.Column('projection_years', sa.Integer(), nullable=False, server_default='10'),
        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('financial_profiles')
