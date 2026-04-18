"""ImportedEvent model: dedup ledger for any CSV-imported row.

Every BUY/SELL/DIV/cash-flow/credit-card row we ingest is hashed and
recorded here so re-importing the same file is a no-op. The hash is
content-based (source + account + date + transaction code + amount +
description) and does not depend on the target table.
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
    source: Mapped[str] = mapped_column(String(50))
    target_table: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<ImportedEvent(hash={self.hash[:8]}..., "
            f"target={self.target_table}:{self.target_id})>"
        )
