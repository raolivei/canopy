"""Initial portfolio schema

Revision ID: 001
Revises: 
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assets table with all asset types
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.Enum(
            'stock', 'etf', 'crypto', 'bond', 'cash',
            'bank_account', 'bank_checking', 'bank_savings',
            'retirement_rrsp', 'retirement_tfsa', 'retirement_fhsa', 'retirement_dpsp',
            'retirement_401k', 'retirement_ira', 'retirement_roth_ira',
            'real_estate', 'crowdfunding', 'private_equity',
            'liability_credit_card', 'liability_loan', 'liability_mortgage',
            'liability_car_loan', 'liability_line_of_credit',
            'other',
            name='assettype'
        ), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # Institution and location
        sa.Column('institution', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True),
        # Liability tracking
        sa.Column('is_liability', sa.Boolean(), nullable=False, server_default='false'),
        # Ownership percentage
        sa.Column('ownership_percentage', sa.Numeric(precision=5, scale=4), nullable=False, server_default='1.0'),
        # Sync source
        sa.Column('sync_source', sa.String(length=50), nullable=True, server_default='MANUAL'),
        sa.Column('external_account_id', sa.String(length=100), nullable=True),
        # Price tracking
        sa.Column('current_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('price_updated_at', sa.DateTime(timezone=True), nullable=True),
        # Liability-specific fields
        sa.Column('interest_rate', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('credit_limit', sa.Numeric(precision=18, scale=2), nullable=True),
        # Notes
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_symbol'), 'assets', ['symbol'], unique=True)
    
    # Create lots table
    op.create_table(
        'lots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('price_per_unit', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('fees', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('account', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_sold', sa.Boolean(), nullable=False),
        sa.Column('sold_date', sa.Date(), nullable=True),
        sa.Column('sold_price_per_unit', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('sold_fees', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lots_asset_id'), 'lots', ['asset_id'], unique=False)
    
    # Create dividends table
    op.create_table(
        'dividends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('dividend_type', sa.Enum('cash', 'stock', 'reinvested', name='dividendtype'), nullable=False),
        sa.Column('shares_received', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dividends_asset_id'), 'dividends', ['asset_id'], unique=False)
    op.create_index(op.f('ix_dividends_payment_date'), 'dividends', ['payment_date'], unique=False)
    
    # Create price_history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_history_asset_id'), 'price_history', ['asset_id'], unique=False)
    op.create_index(op.f('ix_price_history_fetched_at'), 'price_history', ['fetched_at'], unique=False)
    op.create_index('ix_price_history_asset_fetched', 'price_history', ['asset_id', 'fetched_at'], unique=False)
    
    # Create portfolio_snapshots table
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_value', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('total_cost_basis', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portfolio_snapshots_snapshot_date'), 'portfolio_snapshots', ['snapshot_date'], unique=True)
    
    # Create snapshot_holdings table
    op.create_table(
        'snapshot_holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('market_value', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('cost_basis', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('price_at_snapshot', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['portfolio_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_snapshot_holdings_asset_id'), 'snapshot_holdings', ['asset_id'], unique=False)
    op.create_index(op.f('ix_snapshot_holdings_snapshot_id'), 'snapshot_holdings', ['snapshot_id'], unique=False)
    op.create_index('ix_snapshot_holdings_snapshot_asset', 'snapshot_holdings', ['snapshot_id', 'asset_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_snapshot_holdings_snapshot_asset', table_name='snapshot_holdings')
    op.drop_index(op.f('ix_snapshot_holdings_snapshot_id'), table_name='snapshot_holdings')
    op.drop_index(op.f('ix_snapshot_holdings_asset_id'), table_name='snapshot_holdings')
    op.drop_table('snapshot_holdings')
    
    op.drop_index(op.f('ix_portfolio_snapshots_snapshot_date'), table_name='portfolio_snapshots')
    op.drop_table('portfolio_snapshots')
    
    op.drop_index('ix_price_history_asset_fetched', table_name='price_history')
    op.drop_index(op.f('ix_price_history_fetched_at'), table_name='price_history')
    op.drop_index(op.f('ix_price_history_asset_id'), table_name='price_history')
    op.drop_table('price_history')
    
    op.drop_index(op.f('ix_dividends_payment_date'), table_name='dividends')
    op.drop_index(op.f('ix_dividends_asset_id'), table_name='dividends')
    op.drop_table('dividends')
    
    op.drop_index(op.f('ix_lots_asset_id'), table_name='lots')
    op.drop_table('lots')
    
    op.drop_index(op.f('ix_assets_symbol'), table_name='assets')
    op.drop_table('assets')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS assettype')
    op.execute('DROP TYPE IF EXISTS dividendtype')
