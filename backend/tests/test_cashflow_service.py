"""CashflowService on the calculation contract: calendar months, exact Decimals, explicit FX."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.db.models.fx_rate import FxRate
from backend.db.models.transaction import Transaction as TransactionModel
from backend.services.cashflow_service import CashflowService


def tx(db, when: datetime, amount: str, tx_type: str, *, currency: str = "CAD", category: str | None = None):
    row = TransactionModel(
        description=f"{tx_type} {amount}",
        amount=Decimal(amount),
        currency=currency,
        type=tx_type,
        date=when,
        category=category,
    )
    db.add(row)
    return row


@pytest.fixture
def three_month_transactions(db):
    """March-May 2026: income 5000 each month; expenses 2000 / 2500 / 3000."""
    tx(db, datetime(2026, 3, 15), "5000.00", "income", category="Salary")
    tx(db, datetime(2026, 3, 10), "-800.00", "expense", category="Food & Dining")
    tx(db, datetime(2026, 3, 1), "-1200.00", "expense", category="Housing")
    tx(db, datetime(2026, 4, 15), "5000.00", "income", category="Salary")
    tx(db, datetime(2026, 4, 10), "-900.00", "expense", category="Food & Dining")
    tx(db, datetime(2026, 4, 1), "-1200.00", "expense", category="Housing")
    tx(db, datetime(2026, 4, 5), "-400.00", "expense", category="Bills & Utilities")
    tx(db, datetime(2026, 5, 15), "5000.00", "income", category="Salary")
    tx(db, datetime(2026, 5, 10), "-1000.00", "expense", category="Food & Dining")
    tx(db, datetime(2026, 5, 1), "-1200.00", "expense", category="Housing")
    tx(db, datetime(2026, 5, 20), "-800.00", "expense", category="Transportation")
    db.commit()


def test_monthly_summary_exact_per_month(db, three_month_transactions):
    result = CashflowService(db).get_monthly_summary(date(2026, 3, 1), date(2026, 5, 31))

    assert [(m["month"], m["income"], m["expenses"], m["net"]) for m in result] == [
        ("2026-03", Decimal("5000.00"), Decimal("2000.00"), Decimal("3000.00")),
        ("2026-04", Decimal("5000.00"), Decimal("2500.00"), Decimal("2500.00")),
        ("2026-05", Decimal("5000.00"), Decimal("3000.00"), Decimal("2000.00")),
    ]
    march = result[0]
    assert march["currency"] == "CAD"
    assert march["savings_rate"] == pytest.approx(0.6)
    assert march["by_currency"] == {
        "CAD": {"income": Decimal("5000.00"), "expenses": Decimal("2000.00"), "net": Decimal("3000.00")}
    }
    assert march["fx_complete"] is True
    assert march["fx"] == []


def test_monthly_summary_zero_fills_missing_months(db):
    tx(db, datetime(2026, 2, 10), "100.00", "income")
    db.commit()

    result = CashflowService(db).get_monthly_summary(date(2026, 1, 1), date(2026, 3, 31))

    assert [m["month"] for m in result] == ["2026-01", "2026-02", "2026-03"]
    assert result[0]["income"] == Decimal("0.00")
    assert result[1]["income"] == Decimal("100.00")
    assert result[0]["savings_rate"] is None


def test_monthly_summary_rejects_reversed_range(db):
    with pytest.raises(ValueError):
        CashflowService(db).get_monthly_summary(date(2026, 2, 1), date(2026, 1, 1))


def test_monthly_summary_keeps_currencies_apart_without_rate(db):
    tx(db, datetime(2026, 3, 1), "-100.00", "expense", currency="CAD")
    tx(db, datetime(2026, 3, 2), "-100.00", "expense", currency="USD")
    db.commit()

    march = CashflowService(db).get_monthly_summary(date(2026, 3, 1), date(2026, 3, 31))[0]

    assert march["expenses"] == Decimal("100.00")  # USD is not folded in
    assert march["fx_complete"] is False
    assert march["unconverted"]["USD"]["expenses"] == Decimal("100.00")
    assert set(march["by_currency"]) == {"CAD", "USD"}


def test_monthly_summary_converts_with_month_end_rate_and_provenance(db):
    tx(db, datetime(2026, 3, 1), "-100.00", "expense", currency="CAD")
    tx(db, datetime(2026, 3, 2), "-100.00", "expense", currency="USD")
    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 3, 27), rate=Decimal("1.35000000"), source="bank_of_canada"))
    db.commit()

    march = CashflowService(db).get_monthly_summary(date(2026, 3, 1), date(2026, 3, 31))[0]

    assert march["expenses"] == Decimal("235.00")
    assert march["fx_complete"] is True
    assert march["unconverted"] == {}
    assert march["fx"][0]["as_of"] == date(2026, 3, 27)  # the observation used, not March 31
    assert march["fx"][0]["rate"] == Decimal("1.35000000")


def test_monthly_summary_in_usd(db):
    tx(db, datetime(2026, 3, 1), "-135.00", "expense", currency="CAD")
    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 3, 31), rate=Decimal("1.35000000")))
    db.commit()

    march = CashflowService(db, "USD").get_monthly_summary(date(2026, 3, 1), date(2026, 3, 31))[0]
    assert march["currency"] == "USD"
    assert march["expenses"] == Decimal("100.00")


def test_trend_uses_calendar_months_and_exact_averages(db, three_month_transactions):
    result = CashflowService(db).get_cashflow_trend(months=3, today=date(2026, 5, 31))

    assert result["months"] == 3
    assert [m["month"] for m in result["monthly_data"]] == ["2026-03", "2026-04", "2026-05"]
    assert result["average_income"] == Decimal("5000.00")
    assert result["average_expenses"] == Decimal("2500.00")
    assert result["average_net"] == Decimal("2500.00")
    assert result["trend"] == "stable"  # fewer than 6 months
    assert result["currency"] == "CAD"
    assert result["fx_complete"] is True


def test_trend_window_ends_with_the_month_of_today(db, three_month_transactions):
    result = CashflowService(db).get_cashflow_trend(months=2, today=date(2026, 4, 3))
    assert [m["month"] for m in result["monthly_data"]] == ["2026-03", "2026-04"]


def test_trend_no_data_is_zero_filled(db):
    result = CashflowService(db).get_cashflow_trend(months=12, today=date(2026, 1, 15))

    assert result["trend"] == "no_data"
    assert len(result["monthly_data"]) == 12
    assert result["monthly_data"][0]["month"] == "2025-02"
    assert result["average_income"] == Decimal("0.00")


def test_trend_improving_and_declining(db):
    for month in range(1, 4):
        tx(db, datetime(2026, month, 5), "100.00", "income")
    for month in range(4, 7):
        tx(db, datetime(2026, month, 5), "300.00", "income")
    db.commit()
    assert CashflowService(db).get_cashflow_trend(months=6, today=date(2026, 6, 30))["trend"] == "improving"

    db.query(TransactionModel).delete()
    for month in range(1, 4):
        tx(db, datetime(2026, month, 5), "300.00", "income")
    for month in range(4, 7):
        tx(db, datetime(2026, month, 5), "100.00", "income")
    db.commit()
    assert CashflowService(db).get_cashflow_trend(months=6, today=date(2026, 6, 30))["trend"] == "declining"


def test_category_breakdown_sorted_with_percentages(db, three_month_transactions):
    result = CashflowService(db).get_category_breakdown(month="2026-05")

    assert result["month"] == "2026-05"
    assert result["kind"] == "expense"
    assert result["total"] == Decimal("3000.00")
    assert [(c["category"], c["amount"]) for c in result["categories"]] == [
        ("Housing", Decimal("1200.00")),
        ("Food & Dining", Decimal("1000.00")),
        ("Transportation", Decimal("800.00")),
    ]
    assert result["categories"][0]["percentage"] == pytest.approx(40.0)
    assert result["categories"][1]["percentage"] == pytest.approx(33.333, rel=1e-3)


def test_category_breakdown_income_and_default_month(db, three_month_transactions):
    result = CashflowService(db).get_category_breakdown(kind="income", today=date(2026, 4, 20))

    assert result["month"] == "2026-04"
    assert result["total"] == Decimal("5000.00")
    assert [c["category"] for c in result["categories"]] == ["Salary"]


def test_category_breakdown_empty_month(db):
    result = CashflowService(db).get_category_breakdown(month="2026-01")
    assert result["total"] == Decimal("0.00")
    assert result["categories"] == []


def test_burn_rate_only_counts_months_with_expenses(db, three_month_transactions):
    result = CashflowService(db).calculate_burn_rate(months=6, today=date(2026, 5, 31))

    assert result["months_analyzed"] == 3
    assert result["average_monthly_burn"] == Decimal("2500.00")
    assert result["min_month"] == {"month": "2026-03", "amount": Decimal("2000.00")}
    assert result["max_month"] == {"month": "2026-05", "amount": Decimal("3000.00")}
    assert result["volatility"] == "moderate"  # CV ~16%


def test_burn_rate_empty(db):
    result = CashflowService(db).calculate_burn_rate(months=3, today=date(2026, 1, 15))
    assert result["months_analyzed"] == 0
    assert result["monthly_breakdown"] == []
    assert result["min_month"] is None
    assert result["volatility"] == "no_data"


@pytest.mark.parametrize(
    "amounts, expected",
    [(["-1000.00"] * 3, "low"), (["-500.00", "-3000.00", "-1500.00"], "high")],
)
def test_burn_rate_volatility(db, amounts, expected):
    for month, amount in enumerate(amounts, start=1):
        tx(db, datetime(2026, month, 15), amount, "expense")
    db.commit()
    assert CashflowService(db).calculate_burn_rate(months=3, today=date(2026, 3, 31))["volatility"] == expected


def test_comparison_month_vs_prior_month(db, three_month_transactions):
    result = CashflowService(db).get_comparison("month", "2026-04")

    assert result["current"]["start"] == date(2026, 4, 1)
    assert result["current"]["end"] == date(2026, 4, 30)
    assert result["prior"]["start"] == date(2026, 3, 1)
    assert result["current"]["expenses"] == Decimal("2500.00")
    assert result["prior"]["expenses"] == Decimal("2000.00")
    assert result["delta"]["expenses"] == Decimal("500.00")
    assert result["delta"]["net"] == Decimal("-500.00")
    assert result["delta"]["savings_rate_points"] == pytest.approx(-10.0)


def test_comparison_quarter_and_year(db, three_month_transactions):
    quarter = CashflowService(db).get_comparison("quarter", "2026-05")
    assert quarter["current"]["start"] == date(2026, 4, 1)
    assert quarter["current"]["end"] == date(2026, 6, 30)
    assert quarter["current"]["expenses"] == Decimal("5500.00")
    assert quarter["prior"]["expenses"] == Decimal("2000.00")

    year = CashflowService(db).get_comparison("year", "2026-05")
    assert year["current"]["expenses"] == Decimal("7500.00")
    assert year["prior"]["income"] == Decimal("0.00")
    assert year["prior"]["savings_rate"] is None
    assert year["delta"]["savings_rate_points"] is None
