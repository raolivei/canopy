"""Add portfolio_reviews and portfolio_review_lines for semi-annual snapshots

Revision ID: 20260401_0005
Revises: 20260201_0003
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260401_0005"
down_revision = "20260201_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolio_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="csv_import"),
        sa.Column("total_value_usd", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("as_of_date", name="uq_portfolio_reviews_as_of_date"),
    )
    op.create_index(
        op.f("ix_portfolio_reviews_as_of_date"),
        "portfolio_reviews",
        ["as_of_date"],
        unique=False,
    )

    op.create_table(
        "portfolio_review_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("region", sa.String(length=16), nullable=False),
        sa.Column("investment", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("currency", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("value_native", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("value_usd", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("pct_region", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("pct_global", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("return_pct", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("div_per_year", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("yield_pct", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("fx_note", sa.String(length=64), nullable=True),
        sa.Column("target_pct", sa.String(length=128), nullable=True),
        sa.Column("delta", sa.String(length=128), nullable=True),
        sa.Column("conviction", sa.SmallInteger(), nullable=True),
        sa.Column("action", sa.String(length=256), nullable=True),
        sa.Column("raw_row", JSONB, nullable=True),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["portfolio_reviews.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_review_lines_review_id"),
        "portfolio_review_lines",
        ["review_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_portfolio_review_lines_region"),
        "portfolio_review_lines",
        ["region"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_portfolio_review_lines_region"), table_name="portfolio_review_lines")
    op.drop_index(op.f("ix_portfolio_review_lines_review_id"), table_name="portfolio_review_lines")
    op.drop_table("portfolio_review_lines")
    op.drop_index(op.f("ix_portfolio_reviews_as_of_date"), table_name="portfolio_reviews")
    op.drop_table("portfolio_reviews")
