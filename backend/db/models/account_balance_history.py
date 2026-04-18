"""AccountBalanceHistory: per-asset end-of-period balance snapshots.

Populated by the CSV auto-importer from the `balance` column of
Wealthsimple statements. Lets the dashboard chart a per-account
timeline without needing daily PortfolioSnapshots.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class AccountBalanceHistory(Base):
    """End-of-period balance for an Asset (bank, brokerage cash, etc.)."""

    __tablename__ = "account_balance_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))
    currency: Mapped[str] = mapped_column(String(10), default="CAD")
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "asset_id", "as_of_date", name="uq_account_balance_asset_date"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountBalanceHistory(asset_id={self.asset_id}, "
            f"as_of={self.as_of_date}, balance={self.balance})>"
        )
