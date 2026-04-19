"""ImportedEvent model: dedup ledger for any CSV-imported row.

Two hashes are recorded per event:

* ``hash`` - per-source fingerprint, captures source-specific fields like
  the raw transaction code or the full bank description. Catches re-uploads
  of the same file from the same source.
* ``canonical_hash`` - source-agnostic fingerprint of the *real-world*
  transaction (``entity_key`` + date + signed amount). Catches the same
  transaction being imported from two different sources (Wealthsimple +
  Monarch, for example).

Both are nullable to allow lazy backfill for pre-existing rows.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ImportedEvent(Base):
    """Ledger row recording a single ingested CSV event."""

    __tablename__ = "imported_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    canonical_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(50))
    target_table: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<ImportedEvent(hash={self.hash[:8]}..., target={self.target_table}:{self.target_id})>"
