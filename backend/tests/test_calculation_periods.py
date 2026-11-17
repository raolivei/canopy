"""Calendar period helpers of the calculation contract."""

from datetime import date, datetime

import pytest

from backend.services.calculation import (
    add_months,
    as_datetime_range,
    month_bounds,
    month_key,
    months_back,
    months_between,
    parse_month,
    period_bounds,
    prior_period_bounds,
    quarter_bounds,
    year_bounds,
)


@pytest.mark.parametrize(
    "value, expected",
    [("2026-03", (2026, 3)), ("2024-12", (2024, 12)), (" 2026-01 ", (2026, 1))],
)
def test_parse_month_accepts_strict_yyyy_mm(value, expected):
    assert parse_month(value) == expected


@pytest.mark.parametrize("value", ["2026-1", "2026-13", "2026-00", "26-01", "2026/01", "", "march"])
def test_parse_month_rejects_malformed_values(value):
    with pytest.raises(ValueError):
        parse_month(value)


def test_month_key_zero_pads():
    assert month_key(2026, 3) == "2026-03"


@pytest.mark.parametrize(
    "start, months, expected",
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),  # leap year
        (date(2026, 3, 31), -1, date(2026, 2, 28)),
        (date(2026, 12, 15), 1, date(2027, 1, 15)),
        (date(2026, 1, 15), -1, date(2025, 12, 15)),
        (date(2026, 5, 31), 12, date(2027, 5, 31)),
    ],
)
def test_add_months_clamps_to_month_end(start, months, expected):
    assert add_months(start, months) == expected


@pytest.mark.parametrize(
    "year, month, expected",
    [
        (2026, 1, (date(2026, 1, 1), date(2026, 2, 1))),
        (2026, 2, (date(2026, 2, 1), date(2026, 3, 1))),
        (2028, 2, (date(2028, 2, 1), date(2028, 3, 1))),
        (2026, 12, (date(2026, 12, 1), date(2027, 1, 1))),
    ],
)
def test_month_bounds_are_half_open_calendar_months(year, month, expected):
    assert month_bounds(year, month) == expected


def test_quarter_and_year_bounds():
    assert quarter_bounds(2026, 1) == (date(2026, 1, 1), date(2026, 4, 1))
    assert quarter_bounds(2026, 4) == (date(2026, 10, 1), date(2027, 1, 1))
    assert year_bounds(2026) == (date(2026, 1, 1), date(2027, 1, 1))
    with pytest.raises(ValueError):
        quarter_bounds(2026, 5)


def test_period_bounds_dispatch():
    assert period_bounds("month", 2026, 5) == (date(2026, 5, 1), date(2026, 6, 1))
    assert period_bounds("quarter", 2026, 5) == (date(2026, 4, 1), date(2026, 7, 1))
    assert period_bounds("year", 2026, 5) == (date(2026, 1, 1), date(2027, 1, 1))
    with pytest.raises(ValueError):
        period_bounds("week", 2026, 5)  # type: ignore[arg-type]


def test_prior_period_bounds_are_contiguous():
    assert prior_period_bounds("month", date(2026, 1, 1)) == (date(2025, 12, 1), date(2026, 1, 1))
    assert prior_period_bounds("quarter", date(2026, 4, 1)) == (date(2026, 1, 1), date(2026, 4, 1))
    assert prior_period_bounds("year", date(2026, 1, 1)) == (date(2025, 1, 1), date(2026, 1, 1))


def test_months_back_counts_calendar_months_oldest_first():
    assert months_back(date(2026, 1, 15), 3) == [(2025, 11), (2025, 12), (2026, 1)]
    assert months_back(date(2026, 3, 1), 1) == [(2026, 3)]
    with pytest.raises(ValueError):
        months_back(date(2026, 3, 1), 0)


def test_months_between_is_inclusive_of_both_ends():
    assert months_between(date(2025, 11, 20), date(2026, 2, 3)) == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]
    assert months_between(date(2026, 2, 3), date(2026, 2, 28)) == [(2026, 2)]


def test_as_datetime_range_is_midnight_to_midnight():
    assert as_datetime_range(date(2026, 1, 1), date(2026, 2, 1)) == (datetime(2026, 1, 1), datetime(2026, 2, 1))
