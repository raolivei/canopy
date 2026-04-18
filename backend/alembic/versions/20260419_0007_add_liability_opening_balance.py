"""Add Liability.opening_balance for credit-card imports without full history

Revision ID: 20260419_0007
Revises: 20260418_0006
Create Date: 2026-04-19

"""
import sqlalchemy as sa

from alembic import op

revision = "20260419_0007"
down_revision = "20260418_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "liabilities",
        sa.Column(
            "opening_balance",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("liabilities", "opening_balance")
