"""Add real estate and liability models for insights.

Revision ID: 002_add_insights_models
Revises: 001
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_insights_models'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE: Columns for assets table (institution, country, is_liability, etc.)
    # are now in the initial migration (001). This migration only adds
    # real estate and liability tables.
    
    # Create real_estate_properties table
    op.create_table(
        'real_estate_properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('country', sa.String(2), nullable=False, server_default='BR'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='BRL'),
        sa.Column('total_contract_value', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('ownership_percentage', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        sa.Column('partner_name', sa.String(100), nullable=True),
        sa.Column('partner_ownership_percentage', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('estimated_market_value', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('value_estimated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('is_delivered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_rented', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('monthly_rent', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create real_estate_payment_series table
    op.create_table(
        'real_estate_payment_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('frequency', sa.String(50), nullable=False, server_default='monthly'),
        sa.Column('total_installments', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('nominal_amount_per_installment', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['real_estate_properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create real_estate_payments table
    op.create_table(
        'real_estate_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('nominal_amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('amount_with_correction', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('amount_paid', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('is_split', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('paid_by_user', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['real_estate_properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['series_id'], ['real_estate_payment_series.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create liabilities table
    op.create_table(
        'liabilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('institution', sa.String(100), nullable=False),
        sa.Column('account_number_last4', sa.String(4), nullable=True),
        sa.Column('liability_type', sa.String(50), nullable=False, server_default='credit_card'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='CAD'),
        sa.Column('country', sa.String(2), nullable=False, server_default='CA'),
        sa.Column('current_balance', sa.Numeric(precision=18, scale=2), nullable=False, server_default='0'),
        sa.Column('balance_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('credit_limit', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('available_credit', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('apr', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('promotional_apr', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('promotional_apr_end_date', sa.Date(), nullable=True),
        sa.Column('original_principal', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('loan_term_months', sa.Integer(), nullable=True),
        sa.Column('loan_start_date', sa.Date(), nullable=True),
        sa.Column('loan_end_date', sa.Date(), nullable=True),
        sa.Column('minimum_payment', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('fixed_payment', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('payment_due_day', sa.Integer(), nullable=True),
        sa.Column('next_payment_due', sa.Date(), nullable=True),
        sa.Column('statement_closing_day', sa.Integer(), nullable=True),
        sa.Column('last_statement_balance', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('last_statement_date', sa.Date(), nullable=True),
        sa.Column('rewards_program', sa.String(100), nullable=True),
        sa.Column('annual_fee', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create liability_balance_history table
    op.create_table(
        'liability_balance_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('liability_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_statement_balance', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['liability_id'], ['liabilities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create liability_payments table
    op.create_table(
        'liability_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('liability_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('principal_amount', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('interest_amount', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['liability_id'], ['liabilities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('ix_liabilities_institution', 'liabilities', ['institution'])
    op.create_index('ix_liabilities_liability_type', 'liabilities', ['liability_type'])
    op.create_index('ix_real_estate_properties_country', 'real_estate_properties', ['country'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_real_estate_properties_country', 'real_estate_properties')
    op.drop_index('ix_liabilities_liability_type', 'liabilities')
    op.drop_index('ix_liabilities_institution', 'liabilities')
    
    # Drop tables in reverse order
    op.drop_table('liability_payments')
    op.drop_table('liability_balance_history')
    op.drop_table('liabilities')
    op.drop_table('real_estate_payments')
    op.drop_table('real_estate_payment_series')
    op.drop_table('real_estate_properties')
    
    # NOTE: Asset columns are now dropped in the initial migration (001)
