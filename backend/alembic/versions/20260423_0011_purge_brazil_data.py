"""Purge legacy Brazil-scoped data (CAD + USD only)

Revision ID: 20260423_0011
Revises: 20260422_0010
Create Date: 2026-04-23

Canopy is now a CAD + USD Canadian investment tracker. Any rows left
over from the pre-0.9.0 multi-region era (country='BR' or
currency='BRL') must be deleted so aggregations stay clean and the
product's scope is reflected in the data.

Order matters: child rows go first so FK-backed deletes don't trip over
CASCADE that isn't declared everywhere. Everything here is an idempotent
``DELETE ... WHERE`` so running the migration against a DB that has no
BR data is a no-op.

The migration is deliberately narrow - it targets the two structured
scope fields (``country``, ``currency``) and does not touch free-text
notes or historical snapshot holdings. Out of scope: any Brazilian real
estate (``real_estate_properties.currency='BRL'``), which is cascaded
through its own payment tables.
"""

from alembic import op

revision = "20260423_0011"
down_revision = "20260422_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- Asset side: wipe BR-scoped assets and their children -------------
    # Gather asset ids first so we can delete children cleanly.
    br_asset_ids = [
        row[0]
        for row in conn.execute(
            _sql("SELECT id FROM assets WHERE country = 'BR' OR currency = 'BRL'")
        ).fetchall()
    ]
    if br_asset_ids:
        _delete_where_in(conn, "account_balance_history", "asset_id", br_asset_ids)
        _delete_where_in(conn, "lots", "asset_id", br_asset_ids)
        _delete_where_in(conn, "dividends", "asset_id", br_asset_ids)
        _delete_where_in(conn, "price_history", "asset_id", br_asset_ids)
        # portfolio_snapshot_holdings may or may not exist depending on
        # when the DB was first created. Guard against missing table.
        if _has_table(conn, "portfolio_snapshot_holdings"):
            _delete_where_in(conn, "portfolio_snapshot_holdings", "asset_id", br_asset_ids)
        _delete_where_in(conn, "assets", "id", br_asset_ids)

    # --- Liability side: wipe BR-scoped liabilities and their children ----
    br_liab_ids = [
        row[0]
        for row in conn.execute(
            _sql("SELECT id FROM liabilities WHERE country = 'BR' OR currency = 'BRL'")
        ).fetchall()
    ]
    if br_liab_ids:
        _delete_where_in(conn, "liability_balance_history", "liability_id", br_liab_ids)
        _delete_where_in(conn, "liability_payments", "liability_id", br_liab_ids)
        _delete_where_in(conn, "liabilities", "id", br_liab_ids)

    # --- Real estate: BRL-denominated properties --------------------------
    if _has_table(conn, "real_estate_properties"):
        br_re_ids = [
            row[0]
            for row in conn.execute(
                _sql(
                    "SELECT id FROM real_estate_properties "
                    "WHERE country = 'BR' OR currency = 'BRL'"
                )
            ).fetchall()
        ]
        if br_re_ids:
            if _has_table(conn, "real_estate_payments"):
                _delete_where_in(
                    conn, "real_estate_payments", "property_id", br_re_ids
                )
            if _has_table(conn, "real_estate_payment_series"):
                _delete_where_in(
                    conn, "real_estate_payment_series", "property_id", br_re_ids
                )
            _delete_where_in(conn, "real_estate_properties", "id", br_re_ids)

    # --- Transactions in BRL (regardless of account) ----------------------
    conn.execute(_sql("DELETE FROM transactions WHERE currency = 'BRL'"))


def downgrade() -> None:
    # Data deletion is not reversible. Left intentionally as a no-op so
    # ``alembic downgrade`` doesn't fail; restore from backup if you need
    # the BR data back.
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sql(text: str):
    """Late import so migrations stay valid at module import time."""
    import sqlalchemy as sa

    return sa.text(text)


def _delete_where_in(conn, table: str, column: str, ids: list[int]) -> None:
    if not ids:
        return
    # Chunk to stay under any driver-level parameter limit.
    chunk = 500
    for i in range(0, len(ids), chunk):
        batch = ids[i : i + chunk]
        placeholders = ", ".join(f":id{k}" for k in range(len(batch)))
        stmt = _sql(f"DELETE FROM {table} WHERE {column} IN ({placeholders})")
        conn.execute(stmt, {f"id{k}": v for k, v in enumerate(batch)})


def _has_table(conn, table: str) -> bool:
    import sqlalchemy as sa

    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()
