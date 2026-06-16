"""Fluent query builder for financial analytics - eliminates SQL boilerplate."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Callable, Iterator
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction as TransactionModel


class TransactionQuery:
    """Fluent interface for building transaction queries."""

    def __init__(self, db: Session):
        self.db = db
        self.filters = []
        self._results = None

    def last_months(self, n: int) -> "TransactionQuery":
        """Filter to last N months."""
        start_date = date.today() - timedelta(days=30 * n)
        self.filters.append(TransactionModel.date >= start_date)
        return self

    def expenses(self) -> "TransactionQuery":
        """Filter to expenses only."""
        self.filters.append(TransactionModel.type == "expense")
        return self

    def income(self) -> "TransactionQuery":
        """Filter to income only."""
        self.filters.append(TransactionModel.type == "income")
        return self

    def with_merchant(self) -> "TransactionQuery":
        """Filter to transactions with merchant."""
        self.filters.append(TransactionModel.merchant.isnot(None))
        return self

    def execute(self) -> list[TransactionModel]:
        """Execute query and return results."""
        if self._results is None:
            query = select(TransactionModel).where(*self.filters)
            self._results = self.db.execute(query).scalars().all()
        return self._results

    def group_by_category(self) -> dict[str, list[TransactionModel]]:
        """Group results by category."""
        groups = defaultdict(list)
        for tx in self.execute():
            category = tx.category or "Uncategorized"
            groups[category].append(tx)
        return dict(groups)

    def group_by_merchant(self) -> dict[str, list[TransactionModel]]:
        """Group results by merchant."""
        groups = defaultdict(list)
        for tx in self.execute():
            if tx.merchant:
                groups[tx.merchant].append(tx)
        return dict(groups)

    def group_by_month(self) -> dict[str, list[TransactionModel]]:
        """Group results by month (YYYY-MM)."""
        groups = defaultdict(list)
        for tx in self.execute():
            month_key = tx.date.strftime("%Y-%m")
            groups[month_key].append(tx)
        return dict(groups)


def calculate_trend(current: float, previous: float, threshold: float = 5.0) -> dict[str, Any]:
    """Calculate trend direction and percent change."""
    if previous == 0:
        return {
            "trend": "new" if current > 0 else "stable",
            "percent_change": None,
        }

    percent_change = ((current - previous) / previous) * 100

    if percent_change > threshold:
        trend = "up"
    elif percent_change < -threshold:
        trend = "down"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "percent_change": percent_change,
    }


def sum_amounts(transactions: list[TransactionModel]) -> float:
    """Sum absolute transaction amounts."""
    return sum(float(abs(tx.amount)) for tx in transactions)


def detect_anomaly(current: float, average: float, threshold: float = 50.0) -> dict[str, Any] | None:
    """Detect if current value is anomalous vs average."""
    if average == 0:
        return None

    percent_above = ((current - average) / average) * 100

    if percent_above > threshold:
        return {
            "flag": "unusual_high",
            "percent_above_average": percent_above,
            "vs_average": average,
        }
    elif percent_above < -threshold:
        return {
            "flag": "unusual_low",
            "percent_above_average": abs(percent_above),
            "vs_average": average,
        }

    return None
