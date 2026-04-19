"""Allow multi-currency account balance snapshots

Revision ID: 20260421_0009
Revises: 20260420_0008
Create Date: 2026-04-21

Widen ``uq_account_balance_asset_date`` to include ``currency`` so a single
Wealthsimple investment account can carry both its CAD and its USD cash
sub-balance on the same statement-end date. The app still aggregates net
worth in CAD; non-CAD rows are preserved for later display on account
detail and are filtered out at aggregation time.
"""

from alembic import op

revision = "20260421_0009"
down_revision = "20260420_0008"
branch_labels = None
depends_on = None


OLD_NAME = "uq_account_balance_asset_date"
NEW_NAME = "uq_account_balance_asset_date_currency"
TABLE = "account_balance_history"


def upgrade() -> None:
    op.drop_constraint(OLD_NAME, TABLE, type_="unique")
    op.create_unique_constraint(
        NEW_NAME,
        TABLE,
        ["asset_id", "as_of_date", "currency"],
    )


def downgrade() -> None:
    # NOTE: downgrade will fail if multi-currency rows exist for the same
    # (asset_id, as_of_date). That is intentional — losing data silently is
    # worse than forcing the operator to dedupe first.
    op.drop_constraint(NEW_NAME, TABLE, type_="unique")
    op.create_unique_constraint(
        OLD_NAME,
        TABLE,
        ["asset_id", "as_of_date"],
    )
