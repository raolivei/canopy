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
    # Create assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.Enum('stock', 'etf', 'crypto', 'bond', 'cash', 'other', name='assettype'), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('price_updated_at', sa.DateTime(timezone=True), nullable=True),
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
