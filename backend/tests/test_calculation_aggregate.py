"""SQL-side aggregation against the SQLite test engine."""

from datetime import date, datetime
from decimal import Decimal

from backend.db.models.fx_rate import FxRate
from backend.db.models.transaction import Transaction
from backend.services.calculation import (
    CurrencyFlow,
    bucket_by_category,
    bucket_by_month,
    monthly_flows,
    months_back,
    rate_lookup,
    zero_fill,
)


def tx(db, when: datetime, amount: str, tx_type: str, *, currency: str = "CAD", category: str | None = None):
    row = Transaction(
        description=f"{tx_type} {amount}",
        amount=Decimal(amount),
        currency=currency,
        type=tx_type,
        date=when,
        category=category,
    )
    db.add(row)
    return row


def test_last_day_of_month_is_included_and_next_month_excluded(db):
    tx(db, datetime(2026, 1, 31, 23, 0), "-100.00", "expense")
    tx(db, datetime(2026, 2, 1, 0, 0), "-7.00", "expense")
    tx(db, datetime(2026, 1, 1, 0, 0), "3000.00", "income")
    db.commit()

    rows = monthly_flows(db, date(2026, 1, 1), date(2026, 2, 1))

    assert [(r.month_key, r.kind, r.total) for r in rows] == [
        ("2026-01", "expense", Decimal("100.00")),
        ("2026-01", "income", Decimal("3000.00")),
    ]


def test_transfers_and_trades_are_excluded(db):
    tx(db, datetime(2026, 3, 5), "-500.00", "transfer")
    tx(db, datetime(2026, 3, 6), "-2000.00", "buy")
    tx(db, datetime(2026, 3, 7), "2000.00", "sell")
    tx(db, datetime(2026, 3, 8), "-20.00", "expense")
    db.commit()

    rows = monthly_flows(db, date(2026, 3, 1), date(2026, 4, 1))

    assert [(r.kind, r.total, r.count) for r in rows] == [("expense", Decimal("20.00"), 1)]


def test_currencies_are_never_summed_together(db):
    tx(db, datetime(2026, 3, 1), "-100.00", "expense", currency="CAD")
    tx(db, datetime(2026, 3, 2), "-100.00", "expense", currency="USD")
    tx(db, datetime(2026, 3, 3), "50.00", "income", currency="usd")
    db.commit()

    buckets = bucket_by_month(monthly_flows(db, date(2026, 3, 1), date(2026, 4, 1)))

    assert buckets == {
        "2026-03": {
            "CAD": CurrencyFlow(Decimal("100.00") * 0, Decimal("100.00")),
            "USD": CurrencyFlow(Decimal("50.00"), Decimal("100.00")),
        }
    }


def test_sign_convention_does_not_matter_only_type(db):
    tx(db, datetime(2026, 3, 1), "-40.00", "expense")  # Monarch style
    tx(db, datetime(2026, 3, 2), "60.00", "expense")  # CSV style
    tx(db, datetime(2026, 3, 3), "-10.00", "income")  # wrong sign, still income
    db.commit()

    flows = bucket_by_month(monthly_flows(db, date(2026, 3, 1), date(2026, 4, 1)))["2026-03"]["CAD"]

    assert flows.expenses == Decimal("100.00")
    assert flows.income == Decimal("10.00")


def test_cent_sums_are_exact(db):
    for amount in ("-0.10", "-0.20", "-0.30"):
        tx(db, datetime(2026, 3, 1), amount, "expense")
    db.commit()

    rows = monthly_flows(db, date(2026, 3, 1), date(2026, 4, 1))

    assert rows[0].total == Decimal("0.60")
    assert rows[0].count == 3


def test_category_grouping_and_filter(db):
    tx(db, datetime(2026, 3, 1), "-10.00", "expense", category="Groceries")
    tx(db, datetime(2026, 3, 2), "-15.00", "expense", category="Groceries")
    tx(db, datetime(2026, 3, 3), "-5.00", "expense", category=None)
    tx(db, datetime(2026, 3, 4), "-99.00", "expense", category="Dining")
    db.commit()

    by_category = bucket_by_category(monthly_flows(db, date(2026, 3, 1), date(2026, 4, 1), by_category=True))
    assert by_category["Groceries"]["CAD"].expenses == Decimal("25.00")
    assert by_category["Uncategorized"]["CAD"].expenses == Decimal("5.00")
    assert by_category["Dining"]["CAD"].expenses == Decimal("99.00")

    only = monthly_flows(db, date(2026, 3, 1), date(2026, 4, 1), by_category=True, categories=["Groceries"])
    assert [r.category for r in only] == ["Groceries"]


def test_zero_fill_keeps_every_calendar_month(db):
    tx(db, datetime(2026, 1, 10), "-10.00", "expense")
    db.commit()

    months = months_back(date(2026, 3, 15), 3)
    filled = zero_fill(bucket_by_month(monthly_flows(db, date(2026, 1, 1), date(2026, 4, 1))), months)

    assert list(filled) == ["2026-01", "2026-02", "2026-03"]
    assert filled["2026-02"] == {}
    assert filled["2026-03"] == {}


def test_rate_lookup_returns_prior_observation_with_provenance(db):
    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 3, 27), rate=Decimal("1.36000000"), source="bank_of_canada"))
    db.commit()
    lookup = rate_lookup(db)

    quote = lookup(date(2026, 3, 29))  # weekend: falls back to the Friday observation
    assert quote is not None
    assert quote.rate == Decimal("1.36000000")
    assert quote.as_of == date(2026, 3, 27)
    assert quote.source == "bank_of_canada"
    assert lookup(date(2026, 3, 26)) is None
