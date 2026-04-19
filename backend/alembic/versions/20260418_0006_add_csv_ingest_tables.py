"""Add imported_events (dedup ledger) and account_balance_history

Revision ID: 20260418_0006
Revises: 20260401_0005
Create Date: 2026-04-18

"""

import sqlalchemy as sa

from alembic import op

revision = "20260418_0006"
down_revision = "20260401_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "imported_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("target_table", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash", name="uq_imported_events_hash"),
    )
    op.create_index(
        op.f("ix_imported_events_hash"),
        "imported_events",
        ["hash"],
        unique=False,
    )

    op.create_table(
        "account_balance_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="CAD"),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "as_of_date", name="uq_account_balance_asset_date"),
    )
    op.create_index(
        op.f("ix_account_balance_history_asset_id"),
        "account_balance_history",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_account_balance_history_as_of_date"),
        "account_balance_history",
        ["as_of_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_account_balance_history_as_of_date"),
        table_name="account_balance_history",
    )
    op.drop_index(
        op.f("ix_account_balance_history_asset_id"),
        table_name="account_balance_history",
    )
    op.drop_table("account_balance_history")
    op.drop_index(op.f("ix_imported_events_hash"), table_name="imported_events")
    op.drop_table("imported_events")
