"""Currency exchange ledger: one row per conversion between the user's own balances.

Exchanges are a standalone log. They never create ``Transaction`` rows, so
cash flow, budgets and net worth are unaffected. Unlike the rest of Canopy
(CAD/USD only), both legs accept any ISO 4217 code; reporting still converts
only CAD/USD and leaves other currencies unconverted.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base

EXCHANGE_PROVIDERS = ("wise", "remitly", "instarem", "bank", "other")
EXCHANGE_SOURCES = ("manual", "wise_csv", "remitly_csv", "instarem_csv")


class Exchange(Base):
    """A currency conversion: ``from_amount`` in ``from_currency`` became ``to_amount`` in ``to_currency``."""

    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)

    from_currency: Mapped[str] = mapped_column(String(3))
    from_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    to_currency: Mapped[str] = mapped_column(String(3))
    to_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    fee_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    # Rate the provider quoted (1 from_currency in to_currency); the effective
    # rate is always derived from the amounts.
    quoted_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)

    from_asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    to_asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    from_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    to_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual", server_default="manual")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "uq_exchanges_provider_external_id",
            "provider",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
            sqlite_where=text("external_id IS NOT NULL"),
        ),
    )

    @property
    def effective_rate(self) -> Decimal:
        """1 ``from_currency`` in ``to_currency``, from the amounts actually exchanged."""
        return Decimal(str(self.to_amount)) / Decimal(str(self.from_amount))
