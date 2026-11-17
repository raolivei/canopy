"""Calendar period helpers.

Every range in this module is **half-open**: ``(start, end_exclusive)``. A
transaction belongs to a period when ``start <= date < end_exclusive``. This
is what makes the last day of a month count, regardless of the time of day
stored on the row. No helper here approximates a month as 30 days.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, time
from typing import Literal

PeriodKind = Literal["month", "quarter", "year"]


def parse_month(value: str) -> tuple[int, int]:
    """Parse ``YYYY-MM`` strictly into ``(year, month)``.

    Raises ``ValueError`` for anything else, including ``2026-1`` or
    ``2026-13``.
    """
    try:
        year_text, month_text = value.strip().split("-")
        if len(year_text) != 4 or len(month_text) != 2:
            raise ValueError
        year, month = int(year_text), int(month_text)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid month {value!r}; expected YYYY-MM") from exc
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month {value!r}; month must be 01-12")
    return year, month


def month_key(year: int, month: int) -> str:
    """``(2026, 3)`` -> ``"2026-03"``."""
    return f"{year:04d}-{month:02d}"


def add_months(day: date, months: int) -> date:
    """Shift ``day`` by ``months`` calendar months, clamping to the month end.

    ``add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)``.
    """
    total = day.year * 12 + (day.month - 1) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """First day of the month and first day of the next month."""
    start = date(year, month, 1)
    return start, add_months(start, 1)


def quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    """Bounds of calendar quarter ``quarter`` (1-4) in ``year``."""
    if not 1 <= quarter <= 4:
        raise ValueError(f"quarter must be 1-4, got {quarter}")
    start = date(year, 3 * (quarter - 1) + 1, 1)
    return start, add_months(start, 3)


def year_bounds(year: int) -> tuple[date, date]:
    """Jan 1 of ``year`` and Jan 1 of the following year."""
    return date(year, 1, 1), date(year + 1, 1, 1)


def period_bounds(kind: PeriodKind, year: int, month: int = 1) -> tuple[date, date]:
    """Bounds of the ``kind`` period that contains ``year``/``month``."""
    if kind == "month":
        return month_bounds(year, month)
    if kind == "quarter":
        return quarter_bounds(year, (month - 1) // 3 + 1)
    if kind == "year":
        return year_bounds(year)
    raise ValueError(f"Unknown period kind {kind!r}")


def prior_period_bounds(kind: PeriodKind, start: date) -> tuple[date, date]:
    """Bounds of the period of the same ``kind`` immediately before ``start``.

    ``start`` must be the first day of a period as returned by
    :func:`period_bounds`.
    """
    length = {"month": 1, "quarter": 3, "year": 12}[kind]
    prior_start = add_months(start, -length)
    return prior_start, start


def months_between(start: date, end: date) -> list[tuple[int, int]]:
    """All ``(year, month)`` pairs from ``start``'s month to ``end``'s month inclusive."""
    out: list[tuple[int, int]] = []
    current = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while current <= last:
        out.append((current.year, current.month))
        current = add_months(current, 1)
    return out


def months_back(end: date, count: int) -> list[tuple[int, int]]:
    """The ``count`` calendar months ending with ``end``'s month, oldest first.

    ``months_back(date(2026, 1, 15), 3) == [(2025, 11), (2025, 12), (2026, 1)]``.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    last = date(end.year, end.month, 1)
    first = add_months(last, -(count - 1))
    return months_between(first, last)


def as_datetime_range(start: date, end_exclusive: date) -> tuple[datetime, datetime]:
    """Midnight-to-midnight datetimes for comparing against DateTime columns.

    Boundaries are evaluated in the clock the rows were stored in (importers
    write date-only values, so this is the calendar date of the transaction).
    """
    return datetime.combine(start, time.min), datetime.combine(end_exclusive, time.min)
