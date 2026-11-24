"""Add exchanges table (currency exchange ledger)

Revision ID: 20261123_0017
Revises: 20260616_0016
Create Date: 2026-11-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20261123_0017'
down_revision = '20260616_0016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the exchanges table."""
    op.create_table(
        'exchanges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('from_currency', sa.String(3), nullable=False),
        sa.Column('from_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('to_currency', sa.String(3), nullable=False),
        sa.Column('to_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('fee_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('fee_currency', sa.String(3), nullable=True),
        sa.Column('quoted_rate', sa.Numeric(18, 8), nullable=True),
        sa.Column('from_asset_id', sa.Integer(), sa.ForeignKey('assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('to_asset_id', sa.Integer(), sa.ForeignKey('assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_label', sa.String(200), nullable=True),
        sa.Column('to_label', sa.String(200), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('source', sa.String(20), nullable=False, server_default='manual'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_exchanges_date', 'exchanges', ['date'])
    op.create_index('ix_exchanges_provider', 'exchanges', ['provider'])
    op.create_index(
        'uq_exchanges_provider_external_id',
        'exchanges',
        ['provider', 'external_id'],
        unique=True,
        postgresql_where=sa.text('external_id IS NOT NULL'),
    )


def downgrade() -> None:
    """Drop the exchanges table."""
    op.drop_index('uq_exchanges_provider_external_id', table_name='exchanges')
    op.drop_index('ix_exchanges_provider', table_name='exchanges')
    op.drop_index('ix_exchanges_date', table_name='exchanges')
    op.drop_table('exchanges')
