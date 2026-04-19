"""CAD-only portfolio reviews: drop region/currency/FX columns, rename USD->CAD

Revision ID: 20260420_0008
Revises: 20260419_0007
Create Date: 2026-04-20

Canopy is Canadian-investments-only. Strip multi-region / multi-currency
columns from portfolio_reviews + portfolio_review_lines:
  - rename ``total_value_usd`` -> ``total_value_cad``
  - rename ``value_usd``       -> ``value_cad``
  - drop ``region``, ``currency``, ``value_native``, ``pct_region``, ``fx_note``

Safe to run: the app has no committed portfolio_review data in production
(fresh DB after the recent data reset). For any legacy USD values still in
the DB we preserve them byte-for-byte via the rename.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260420_0008"
down_revision = "20260419_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # portfolio_reviews
    op.alter_column(
        "portfolio_reviews",
        "total_value_usd",
        new_column_name="total_value_cad",
    )

    # portfolio_review_lines
    op.alter_column(
        "portfolio_review_lines",
        "value_usd",
        new_column_name="value_cad",
    )

    with op.batch_alter_table("portfolio_review_lines") as batch:
        batch.drop_column("region")
        batch.drop_column("currency")
        batch.drop_column("value_native")
        batch.drop_column("pct_region")
        batch.drop_column("fx_note")


def downgrade() -> None:
    op.alter_column(
        "portfolio_reviews",
        "total_value_cad",
        new_column_name="total_value_usd",
    )
    op.alter_column(
        "portfolio_review_lines",
        "value_cad",
        new_column_name="value_usd",
    )

    with op.batch_alter_table("portfolio_review_lines") as batch:
        batch.add_column(
            sa.Column("region", sa.String(length=16), nullable=False, server_default="CA")
        )
        batch.add_column(
            sa.Column("currency", sa.String(length=16), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("value_native", sa.Numeric(precision=18, scale=4), nullable=True)
        )
        batch.add_column(
            sa.Column("pct_region", sa.Numeric(precision=10, scale=6), nullable=True)
        )
        batch.add_column(sa.Column("fx_note", sa.String(length=64), nullable=True))
