"""Add transaction_rules table for automatic categorization

Revision ID: 20260616_0016
Revises: 20260616_0015
Create Date: 2026-06-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260616_0016'
down_revision = '20260616_0015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create transaction_rules table."""

    # Create transaction_rules table
    op.create_table(
        'transaction_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('stop_on_match', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('match_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for efficient querying and sorting
    op.create_index('ix_transaction_rules_active', 'transaction_rules', ['active'])
    op.create_index('ix_transaction_rules_priority', 'transaction_rules', ['priority'])


def downgrade() -> None:
    """Drop transaction_rules table."""

    # Drop indexes
    op.drop_index('ix_transaction_rules_priority', table_name='transaction_rules')
    op.drop_index('ix_transaction_rules_active', table_name='transaction_rules')

    # Drop table
    op.drop_table('transaction_rules')
