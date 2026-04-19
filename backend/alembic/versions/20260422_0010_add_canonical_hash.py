"""Add canonical_hash to imported_events for cross-source dedup

Revision ID: 20260422_0010
Revises: 20260421_0009
Create Date: 2026-04-22

Adds a second, source-agnostic fingerprint to the imported-events ledger.

The existing ``hash`` column stores a per-source fingerprint
(sha256(source | account_key | date | raw_code | amount | description))
and catches re-uploads of the same file. It cannot catch the same
real-world transaction being imported from two different sources
(Wealthsimple + Monarch) because the inputs differ.

``canonical_hash`` is defined as sha256(``entity_key|date|amount``)
where ``entity_key`` is a stable, cross-source identifier for the Canopy
asset/liability the event pertains to (e.g. ``asset:12`` / ``liability:3``).
It is computed by every importer, checked before inserting, and skipped
if it already exists.

Backfill: for existing ``wealthsimple_csv`` events we cannot reconstruct
``entity_key`` without joining through Transaction -> account label ->
Asset/Liability. Rather than do that fragile join in SQL, we leave the
column nullable and compute it lazily on the next ingest (the importer
will re-record canonical hashes as it sees them). New rows populate it.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260422_0010"
down_revision = "20260421_0009"
branch_labels = None
depends_on = None


TABLE = "imported_events"
COLUMN = "canonical_hash"
INDEX = "ix_imported_events_canonical_hash"


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column(COLUMN, sa.String(length=64), nullable=True),
    )
    op.create_index(INDEX, TABLE, [COLUMN])


def downgrade() -> None:
    op.drop_index(INDEX, table_name=TABLE)
    op.drop_column(TABLE, COLUMN)
