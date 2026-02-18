"""Add transactions table

Revision ID: 20260201_0003
Revises: 20260131_0002
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = '20260201_0003'
down_revision = '002_add_insights_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transactions table using String for type column
    # (avoids issues with existing enum types)
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='CAD'),
        sa.Column('type', sa.String(length=20), nullable=False, server_default='expense'),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('account', sa.String(length=200), nullable=True),
        sa.Column('merchant', sa.String(length=200), nullable=True),
        sa.Column('original_statement', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', ARRAY(sa.String()), nullable=True),
        sa.Column('ticker', sa.String(length=20), nullable=True),
        sa.Column('shares', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('price_per_share', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('fees', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('import_id', sa.String(length=100), nullable=True),
        sa.Column('import_source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_transactions_date', 'transactions', ['date'])
    op.create_index('ix_transactions_category', 'transactions', ['category'])
    op.create_index('ix_transactions_type', 'transactions', ['type'])
    op.create_index('ix_transactions_account', 'transactions', ['account'])
    op.create_index('ix_transactions_merchant', 'transactions', ['merchant'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_transactions_merchant', 'transactions')
    op.drop_index('ix_transactions_account', 'transactions')
    op.drop_index('ix_transactions_type', 'transactions')
    op.drop_index('ix_transactions_category', 'transactions')
    op.drop_index('ix_transactions_date', 'transactions')
    
    # Drop table
    op.drop_table('transactions')
    
    # Drop enum
    sa.Enum(name='transactiontype').drop(op.get_bind(), checkfirst=True)
