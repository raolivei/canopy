"""SQL-side monthly aggregation of transaction flows.

Grouping happens in the database (year, month, currency, type[, category])
so result size scales with the number of buckets, not rows. Works on
PostgreSQL and on the SQLite engine used in tests: ``extract`` compiles to
``EXTRACT`` and ``CAST(STRFTIME(...) AS INTEGER)`` respectively.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from backend.db.models.transaction import Transaction
from backend.services import fx
from backend.services.calculation.flows import FLOW_TYPES, INCOME_TYPES, FlowKind
from backend.services.calculation.money import CurrencyFlow, FxQuote, RateLookup, quantize
from backend.services.calculation.periods import as_datetime_range, month_key
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

UNCATEGORIZED = "Uncategorized"
DEFAULT_CURRENCY = "CAD"


@dataclass(frozen=True)
class FlowRow:
    """One aggregated bucket."""

    year: int
    month: int
    currency: str
    kind: FlowKind
    total: Decimal
    count: int
    category: str | None = None

    @property
    def month_key(self) -> str:
        return month_key(self.year, self.month)


def monthly_flows(
    db: Session,
    start: date,
    end_exclusive: date,
    *,
    by_category: bool = False,
    categories: Iterable[str] | None = None,
) -> list[FlowRow]:
    """Sum income and expense magnitudes per month and currency in ``[start, end_exclusive)``.

    Transfers, buys and sells are excluded in SQL. ``categories`` restricts to
    those category names (``None`` category rows are reported as
    ``"Uncategorized"`` when ``by_category`` is set).
    """
    start_dt, end_dt = as_datetime_range(start, end_exclusive)

    year_col = extract("year", Transaction.date).label("year")
    month_col = extract("month", Transaction.date).label("month")
    currency_col = func.coalesce(Transaction.currency, DEFAULT_CURRENCY).label("currency")
    columns = [
        year_col,
        month_col,
        currency_col,
        Transaction.type.label("type"),
        func.sum(func.abs(Transaction.amount)).label("total"),
        func.count().label("count"),
    ]
    group_by = [year_col, month_col, currency_col, Transaction.type]
    if by_category:
        category_col = func.coalesce(Transaction.category, UNCATEGORIZED).label("category")
        columns.append(category_col)
        group_by.append(category_col)

    stmt = (
        select(*columns)
        .where(
            Transaction.date >= start_dt,
            Transaction.date < end_dt,
            Transaction.type.in_(sorted(FLOW_TYPES)),
        )
        .group_by(*group_by)
    )
    if categories is not None:
        stmt = stmt.where(Transaction.category.in_(list(categories)))

    rows: list[FlowRow] = []
    for row in db.execute(stmt).all():
        kind: FlowKind = "income" if row.type in INCOME_TYPES else "expense"
        rows.append(
            FlowRow(
                year=int(row.year),
                month=int(row.month),
                currency=str(row.currency).upper(),
                kind=kind,
                # SQLite returns REAL sums; go through str() so 0.1 + 0.2 stays 0.30.
                total=quantize(Decimal(str(row.total or 0))),
                count=int(row.count),
                category=row.category if by_category else None,
            )
        )
    rows.sort(key=lambda r: (r.year, r.month, r.currency, r.category or "", r.kind))
    return rows


def bucket_by_month(rows: Iterable[FlowRow]) -> dict[str, dict[str, CurrencyFlow]]:
    """``{"YYYY-MM": {"CAD": CurrencyFlow, ...}, ...}``."""
    buckets: dict[str, dict[str, CurrencyFlow]] = {}
    for row in rows:
        flows = buckets.setdefault(row.month_key, {})
        flows.setdefault(row.currency, CurrencyFlow()).add(row.kind, row.total)
    return buckets


def bucket_by_category(rows: Iterable[FlowRow]) -> dict[str, dict[str, CurrencyFlow]]:
    """``{"Groceries": {"CAD": CurrencyFlow, ...}, ...}`` across all months in ``rows``."""
    buckets: dict[str, dict[str, CurrencyFlow]] = {}
    for row in rows:
        flows = buckets.setdefault(row.category or UNCATEGORIZED, {})
        flows.setdefault(row.currency, CurrencyFlow()).add(row.kind, row.total)
    return buckets


def zero_fill(
    buckets: dict[str, dict[str, CurrencyFlow]],
    months: Iterable[tuple[int, int]],
) -> dict[str, dict[str, CurrencyFlow]]:
    """Return ``buckets`` with an entry for every month in ``months`` (empty dict when no rows)."""
    filled = dict(buckets)
    for year, month in months:
        filled.setdefault(month_key(year, month), {})
    return dict(sorted(filled.items()))


def rate_lookup(db: Session, pair: str = fx.DEFAULT_PAIR) -> RateLookup:
    """A :data:`RateLookup` backed by the cached Bank of Canada rates."""

    def lookup(on_date: date) -> FxQuote | None:
        row = fx.get_rate_row_on(db, on_date, pair)
        if row is None:
            return None
        return FxQuote(pair=row.pair, rate=row.rate, as_of=row.as_of_date, source=row.source)

    return lookup
