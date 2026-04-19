"""Add fx_rates table for Bank of Canada FX cache

Revision ID: 20260424_0012
Revises: 20260423_0011
Create Date: 2026-04-24

Canopy now supports Questrade-style currency views (CAD, USD, Combined
CAD, Combined USD). Combined views need a deterministic FX rate; we
store daily Bank of Canada observations so historical conversion uses
the rate-of-day rather than a global snapshot.

Only the USDCAD pair is populated today. The ``pair`` / ``as_of_date``
shape is kept generic so a future EURCAD or similar can slot in
without another migration.
"""

import sqlalchemy as sa
from alembic import op

revision = "20260424_0012"
down_revision = "20260423_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fx_rates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pair", sa.String(length=6), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("pair", "as_of_date", name="uq_fx_rates_pair_date"),
    )
    op.create_index("ix_fx_rates_pair", "fx_rates", ["pair"])
    op.create_index("ix_fx_rates_as_of_date", "fx_rates", ["as_of_date"])


def downgrade() -> None:
    op.drop_index("ix_fx_rates_as_of_date", table_name="fx_rates")
    op.drop_index("ix_fx_rates_pair", table_name="fx_rates")
    op.drop_table("fx_rates")
