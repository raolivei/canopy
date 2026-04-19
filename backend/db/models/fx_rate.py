"""FxRate: daily closing FX rates cached from Bank of Canada.

Canopy is CAD + USD only. The only pair we currently store is
``USDCAD`` (one US dollar in Canadian dollars, BoC's Valet series
``FXUSDCAD``). The table is modelled generically so additional pairs
could be added later without a schema change.

Rows are fetched on demand by :mod:`backend.services.fx`; the service
hits the Bank of Canada Valet endpoint
(``https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json``),
takes the latest observation plus an optional range backfill, and
UPSERTs per ``(pair, as_of_date)``. Lookups for an arbitrary date
fall back to the most-recent prior observation so weekends / holidays
don't break historical net-worth conversion.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class FxRate(Base):
    """One closing FX observation for a currency pair on a given date."""

    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Currency pair in ISO-4217 concatenated form. ``USDCAD`` means the
    # rate is "1 USD in CAD" (so USD -> CAD multiplies, CAD -> USD
    # divides). Store uppercase, 6 chars.
    pair: Mapped[str] = mapped_column(String(6), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    # Where the rate came from — right now always "bank_of_canada", but
    # left open so a manual / alternate-source entry is trivially
    # distinguishable later.
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("pair", "as_of_date", name="uq_fx_rates_pair_date"),
    )

    def __repr__(self) -> str:
        return f"<FxRate({self.pair} {self.as_of_date} = {self.rate})>"
