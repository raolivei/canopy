"""Add performance indexes for transaction queries

Revision ID: 20260615_0014
Revises: 20260501_0013
Create Date: 2026-06-15

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260615_0014'
down_revision = '20260501_0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes for common query patterns."""

    # Most common: date range + type filtering
    op.create_index(
        'idx_transactions_date_type',
        'transactions',
        ['date', 'type'],
        postgresql_ops={'date': 'DESC'},
    )

    # Merchant insights (excludes NULL merchants)
    op.execute("""
        CREATE INDEX idx_transactions_merchant_date
        ON transactions(merchant, date DESC)
        WHERE merchant IS NOT NULL
    """)

    # Category analysis
    op.create_index(
        'idx_transactions_category_date',
        'transactions',
        ['category', 'date'],
        postgresql_ops={'date': 'DESC'},
    )

    # Combined for spending patterns (most selective columns first)
    op.create_index(
        'idx_transactions_date_type_category',
        'transactions',
        ['date', 'type', 'category'],
        postgresql_ops={'date': 'DESC'},
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_transactions_date_type_category', table_name='transactions')
    op.drop_index('idx_transactions_category_date', table_name='transactions')
    op.drop_index('idx_transactions_merchant_date', table_name='transactions')
    op.drop_index('idx_transactions_date_type', table_name='transactions')
