"""/v1/cashflow exercised through the real application and routing."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.db.models.fx_rate import FxRate
from backend.db.models.transaction import Transaction as TransactionModel


def tx(db, when: datetime, amount: str, tx_type: str, *, currency: str = "CAD", category: str | None = None):
    db.add(
        TransactionModel(
            description=f"{tx_type} {amount}",
            amount=Decimal(amount),
            currency=currency,
            type=tx_type,
            date=when,
            category=category,
        )
    )


def test_summary_serializes_money_as_numbers_and_keeps_currencies_apart(client, db):
    tx(db, datetime(2026, 3, 1), "-100.00", "expense", currency="CAD")
    tx(db, datetime(2026, 3, 2), "-100.00", "expense", currency="USD")
    tx(db, datetime(2026, 3, 3), "1000.00", "income")
    db.commit()

    response = client.get("/v1/cashflow/summary", params={"start_date": "2026-03-01", "end_date": "2026-03-31"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_months"] == 1
    assert body["currency"] == "CAD"
    assert body["fx_complete"] is False
    march = body["data"][0]
    assert march["month"] == "2026-03"
    assert march["income"] == 1000.0
    assert march["expenses"] == 100.0  # the USD row is not silently added
    assert march["unconverted"] == {"USD": {"income": 0.0, "expenses": 100.0, "net": -100.0}}
    assert march["by_currency"]["USD"]["expenses"] == 100.0


def test_summary_converts_when_a_rate_exists_and_reports_provenance(client, db):
    tx(db, datetime(2026, 3, 2), "-100.00", "expense", currency="USD")
    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 3, 31), rate=Decimal("1.35000000"), source="bank_of_canada"))
    db.commit()

    march = client.get("/v1/cashflow/summary", params={"start_date": "2026-03-01", "end_date": "2026-03-31"}).json()[
        "data"
    ][0]

    assert march["expenses"] == 135.0
    assert march["fx_complete"] is True
    assert march["fx"] == [
        {
            "from_currency": "USD",
            "to_currency": "CAD",
            "pair": "USDCAD",
            "rate": 1.35,
            "as_of": "2026-03-31",
            "source": "bank_of_canada",
        }
    ]


@pytest.mark.parametrize(
    "when, expected_month",
    [
        (datetime(2026, 1, 31, 23, 59), "2026-01"),
        (datetime(2026, 2, 1, 0, 0), "2026-02"),
        (datetime(2026, 2, 28, 12, 0), "2026-02"),
        (datetime(2028, 2, 29, 12, 0), "2028-02"),
        (datetime(2026, 12, 31, 23, 0), "2026-12"),
        (datetime(2027, 1, 1, 0, 0), "2027-01"),
    ],
)
def test_summary_places_boundary_days_in_the_right_month(client, db, when, expected_month):
    tx(db, when, "-10.00", "expense")
    db.commit()

    start = f"{when.year}-01-01"
    end = f"{when.year + 1}-01-31"
    body = client.get("/v1/cashflow/summary", params={"start_date": start, "end_date": end}).json()
    with_spend = [m["month"] for m in body["data"] if m["expenses"] > 0]
    assert with_spend == [expected_month]


def test_summary_excludes_transfers_and_zero_fills(client, db):
    tx(db, datetime(2026, 2, 5), "-500.00", "transfer")
    tx(db, datetime(2026, 2, 6), "-20.00", "expense")
    db.commit()

    body = client.get("/v1/cashflow/summary", params={"start_date": "2026-01-01", "end_date": "2026-03-31"}).json()

    assert [m["month"] for m in body["data"]] == ["2026-01", "2026-02", "2026-03"]
    assert [m["expenses"] for m in body["data"]] == [0.0, 20.0, 0.0]


@pytest.mark.parametrize(
    "params, status, fragment",
    [
        ({"start_date": "2026-13-01", "end_date": "2026-03-31"}, 400, "start_date"),
        ({"start_date": "2026-03-01", "end_date": "nope"}, 400, "end_date"),
        ({"start_date": "2026-04-01", "end_date": "2026-03-31"}, 400, "on or before"),
        (
            {"start_date": "2026-03-01", "end_date": "2026-03-31", "reporting_currency": "EUR"},
            422,
            "reporting_currency",
        ),
    ],
)
def test_summary_input_validation(client, params, status, fragment):
    response = client.get("/v1/cashflow/summary", params=params)
    assert response.status_code == status
    assert fragment in response.text


def test_trend_and_burn_rate_endpoints(client, db):
    tx(db, datetime(date.today().year, date.today().month, 1), "-50.00", "expense")
    db.commit()

    trend = client.get("/v1/cashflow/trend", params={"months": 3}).json()
    assert trend["months"] == 3
    assert len(trend["monthly_data"]) == 3
    assert trend["monthly_data"][-1]["expenses"] == 50.0
    assert trend["trend"] == "stable"

    burn = client.get("/v1/cashflow/burn-rate", params={"months": 3}).json()
    assert burn["months_analyzed"] == 1
    assert burn["average_monthly_burn"] == 50.0
    assert burn["min_month"]["amount"] == 50.0


def test_categories_by_kind_and_month_validation(client, db):
    tx(db, datetime(2026, 4, 2), "-30.00", "expense", category="Groceries")
    tx(db, datetime(2026, 4, 3), "900.00", "income", category="Salary")
    db.commit()

    expenses = client.get("/v1/cashflow/categories", params={"month": "2026-04"}).json()
    assert expenses["kind"] == "expense"
    assert [(c["category"], c["amount"], c["percentage"]) for c in expenses["categories"]] == [
        ("Groceries", 30.0, 100.0)
    ]

    income = client.get("/v1/cashflow/categories", params={"month": "2026-04", "kind": "income"}).json()
    assert income["total"] == 900.0
    assert [c["category"] for c in income["categories"]] == ["Salary"]

    assert client.get("/v1/cashflow/categories", params={"month": "2026-4"}).status_code == 400
    assert client.get("/v1/cashflow/categories", params={"kind": "transfer"}).status_code == 422


def test_comparison_endpoint(client, db):
    tx(db, datetime(2026, 3, 10), "-200.00", "expense")
    tx(db, datetime(2026, 4, 10), "-250.00", "expense")
    tx(db, datetime(2026, 4, 11), "1000.00", "income")
    db.commit()

    body = client.get("/v1/cashflow/comparison", params={"kind": "month", "reference": "2026-04"}).json()

    assert body["kind"] == "month"
    assert body["current"]["start"] == "2026-04-01"
    assert body["current"]["end"] == "2026-04-30"
    assert body["prior"]["expenses"] == 200.0
    assert body["delta"]["expenses"] == 50.0
    assert body["delta"]["savings_rate_points"] is None  # prior month had no income
    assert client.get("/v1/cashflow/comparison", params={"kind": "week"}).status_code == 422
