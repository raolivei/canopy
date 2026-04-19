"""Admin / maintenance operations (data reset, stats)."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.db.models import (
    AccountBalanceHistory,
    Asset,
    Dividend,
    ImportedEvent,
    Liability,
    LiabilityBalanceHistory,
    LiabilityPayment,
    Lot,
    PortfolioReview,
    PortfolioReviewLine,
    PortfolioSnapshot,
    PriceHistory,
    RealEstatePayment,
    RealEstatePaymentSeries,
    RealEstateProperty,
    SnapshotHolding,
    Transaction,
)
from sqlalchemy.orm import Session

# Deletion order respects FK dependencies: children/associations first,
# parents last. Schema itself is preserved.
_DELETE_ORDER = [
    # Association / history tables first
    ("snapshot_holdings", SnapshotHolding),
    ("portfolio_snapshots", PortfolioSnapshot),
    ("account_balance_history", AccountBalanceHistory),
    ("liability_balance_history", LiabilityBalanceHistory),
    ("liability_payments", LiabilityPayment),
    ("real_estate_payments", RealEstatePayment),
    ("real_estate_payment_series", RealEstatePaymentSeries),
    ("portfolio_review_lines", PortfolioReviewLine),
    ("portfolio_reviews", PortfolioReview),
    ("dividends", Dividend),
    ("lots", Lot),
    ("transactions", Transaction),
    ("price_history", PriceHistory),
    ("imported_events", ImportedEvent),
    # Top-level entities last
    ("real_estate_properties", RealEstateProperty),
    ("liabilities", Liability),
    ("assets", Asset),
]


@dataclass
class ResetReport:
    """Row-count summary from a data reset."""

    deleted: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.deleted.values())


def reset_all_data(db: Session) -> ResetReport:
    """Delete all rows from every data table, preserving the schema.

    Caller is responsible for committing the session. This operation is
    destructive and cannot be undone; any backup / confirmation logic must
    live in the caller (API endpoint, CLI script, etc.).
    """

    report = ResetReport()
    for label, model in _DELETE_ORDER:
        count = db.query(model).delete(synchronize_session=False)
        report.deleted[label] = int(count or 0)
    return report
