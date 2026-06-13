"""Tests for the Cashflow Service (monthly income/expenses/savings metrics).

Coverage focuses on:
* Monthly metrics calculation (income, expenses, savings, rate)
* Trend analysis over 12 months
* Edge cases (no income, zero spending, multi-currency)
* Category aggregation and sorting
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.transaction import Transaction, TransactionType
from backend.services.cashflow_service import CashflowService


@pytest.fixture
def db() -> Session:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


@pytest.fixture
def cashflow_service(db: Session) -> CashflowService:
    """Create CashflowService instance with test database."""
    return CashflowService(db)


def _create_transaction(
    db: Session,
    date: datetime,
    amount: Decimal,
    txn_type: TransactionType,
    category: str | None = None,
    description: str = "Test transaction",
) -> Transaction:
    """Helper to create a transaction in the database."""
    txn = Transaction(
        description=description,
        amount=amount,
        currency="CAD",
        type=txn_type,
        category=category,
        date=date,
        account="Test Account",
    )
    db.add(txn)
    db.flush()
    return txn


# ---------------------------------------------------------------------------
# Monthly Metrics Tests
# ---------------------------------------------------------------------------


def test_monthly_metrics_basic_income_and_expenses(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Monthly metrics should calculate income, expenses, and savings correctly."""
    # Create transactions for June 2026
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("1000.00"),
        TransactionType.EXPENSE,
        "Rent",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 10),
        Decimal("200.00"),
        TransactionType.EXPENSE,
        "Groceries",
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert metrics["month"] == "2026-06"
    assert metrics["income"] == 5000.00
    assert metrics["expenses"] == 1200.00
    assert metrics["savings"] == 3800.00
    assert metrics["savings_rate"] == 76.0
    assert len(metrics["categories"]) == 2
    assert metrics["categories"][0]["category"] == "Rent"
    assert metrics["categories"][0]["amount"] == 1000.00


def test_monthly_metrics_no_income(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Savings rate should be 0 when there's no income."""
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("500.00"),
        TransactionType.EXPENSE,
        "Groceries",
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert metrics["income"] == 0.0
    assert metrics["expenses"] == 500.00
    assert metrics["savings"] == -500.00
    assert metrics["savings_rate"] == 0.0


def test_monthly_metrics_no_expenses(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Savings should equal income when there are no expenses."""
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert metrics["income"] == 5000.00
    assert metrics["expenses"] == 0.0
    assert metrics["savings"] == 5000.00
    assert metrics["savings_rate"] == 100.0


def test_monthly_metrics_ignores_transfers(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Transfers should not be included in income/expense calculations."""
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("1000.00"),
        TransactionType.TRANSFER,
        description="Transfer to savings",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 10),
        Decimal("200.00"),
        TransactionType.EXPENSE,
        "Groceries",
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert metrics["income"] == 5000.00
    assert metrics["expenses"] == 200.00
    assert metrics["savings"] == 4800.00


def test_monthly_metrics_ignores_investment_transactions(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Buy/Sell transactions should not be included in calculations."""
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("1000.00"),
        TransactionType.BUY,
        description="Buy ETF",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 10),
        Decimal("200.00"),
        TransactionType.EXPENSE,
        "Groceries",
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert metrics["income"] == 5000.00
    assert metrics["expenses"] == 200.00


def test_monthly_metrics_categories_sorting(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Top categories should be sorted by amount in descending order."""
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("300.00"),
        TransactionType.EXPENSE,
        "Groceries",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 6),
        Decimal("150.00"),
        TransactionType.EXPENSE,
        "Groceries",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 7),
        Decimal("100.00"),
        TransactionType.EXPENSE,
        "Utilities",
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert metrics["categories"][0]["category"] == "Groceries"
    assert metrics["categories"][0]["amount"] == 450.00
    assert metrics["categories"][1]["category"] == "Utilities"
    assert metrics["categories"][1]["amount"] == 100.00


def test_monthly_metrics_uncategorized_transactions(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Transactions without category should be grouped as 'Uncategorized'."""
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("100.00"),
        TransactionType.EXPENSE,
        category=None,
    )

    metrics = cashflow_service.get_monthly_metrics(2026, 6)

    assert len(metrics["categories"]) == 1
    assert metrics["categories"][0]["category"] == "Uncategorized"
    assert metrics["categories"][0]["amount"] == 100.00


# ---------------------------------------------------------------------------
# Cashflow Trend Tests
# ---------------------------------------------------------------------------


def test_cashflow_trend_12_months(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Trend should return last 12 months of metrics."""
    # Create transactions for June 2026 through May 2027
    base_date = datetime(2026, 6, 1)
    for i in range(12):
        current_date = base_date.replace(month=((5 + i) % 12) + 1)
        year_offset = (5 + i) // 12
        current_date = current_date.replace(year=2026 + year_offset)

        _create_transaction(
            db,
            current_date,
            Decimal("5000.00"),
            TransactionType.INCOME,
            "Salary",
        )
        _create_transaction(
            db,
            current_date + timedelta(days=5),
            Decimal("1000.00"),
            TransactionType.EXPENSE,
            "Rent",
        )

    trend = cashflow_service.get_cashflow_trend(12)

    assert len(trend) == 12
    # All months should have the same metrics
    for metrics in trend:
        assert metrics["income"] == 5000.00
        assert metrics["expenses"] == 1000.00
        assert metrics["savings"] == 4000.00


def test_cashflow_trend_default_12_months(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Default trend should return 12 months when not specified."""
    base_date = datetime(2026, 6, 1)
    for i in range(12):
        current_date = base_date.replace(month=((5 + i) % 12) + 1)
        year_offset = (5 + i) // 12
        current_date = current_date.replace(year=2026 + year_offset)

        _create_transaction(
            db,
            current_date,
            Decimal("5000.00"),
            TransactionType.INCOME,
            "Salary",
        )

    trend = cashflow_service.get_cashflow_trend()

    assert len(trend) == 12


# ---------------------------------------------------------------------------
# Cashflow Summary Tests
# ---------------------------------------------------------------------------


def test_cashflow_summary_basic(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Summary should calculate totals and average over date range."""
    start_date = datetime(2026, 6, 1)
    end_date = datetime(2026, 8, 31)

    # Add transactions for 3 months
    for month in range(6, 9):
        _create_transaction(
            db,
            datetime(2026, month, 1),
            Decimal("5000.00"),
            TransactionType.INCOME,
            "Salary",
        )
        _create_transaction(
            db,
            datetime(2026, month, 5),
            Decimal("1000.00"),
            TransactionType.EXPENSE,
            "Rent",
        )

    summary = cashflow_service.get_cashflow_summary(start_date, end_date)

    assert summary["total_income"] == 15000.00
    assert summary["total_expenses"] == 3000.00
    assert summary["total_savings"] == 12000.00
    assert summary["average_monthly_savings"] == 4000.00


def test_cashflow_summary_trend_calculation(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Summary should calculate trend between first and second halves."""
    start_date = datetime(2026, 6, 1)
    end_date = datetime(2026, 8, 31)

    # First half: high savings
    _create_transaction(
        db,
        datetime(2026, 6, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 6, 5),
        Decimal("500.00"),
        TransactionType.EXPENSE,
        "Rent",
    )

    # Second half: low savings
    _create_transaction(
        db,
        datetime(2026, 8, 1),
        Decimal("5000.00"),
        TransactionType.INCOME,
        "Salary",
    )
    _create_transaction(
        db,
        datetime(2026, 8, 5),
        Decimal("2000.00"),
        TransactionType.EXPENSE,
        "Rent",
    )

    summary = cashflow_service.get_cashflow_summary(start_date, end_date)

    # Trend should be "down" as savings rate decreased
    assert summary["trend"] == "down"


def test_cashflow_summary_stable_trend(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Trend should be 'stable' when savings rate stays similar."""
    start_date = datetime(2026, 6, 1)
    end_date = datetime(2026, 8, 31)

    # Both halves: similar savings rates
    for month in range(6, 9):
        _create_transaction(
            db,
            datetime(2026, month, 1),
            Decimal("5000.00"),
            TransactionType.INCOME,
            "Salary",
        )
        _create_transaction(
            db,
            datetime(2026, month, 5),
            Decimal("1000.00"),
            TransactionType.EXPENSE,
            "Rent",
        )

    summary = cashflow_service.get_cashflow_summary(start_date, end_date)

    assert summary["trend"] == "stable"


def test_cashflow_summary_no_transactions(
    db: Session, cashflow_service: CashflowService
) -> None:
    """Summary should handle empty date ranges gracefully."""
    start_date = datetime(2026, 6, 1)
    end_date = datetime(2026, 8, 31)

    summary = cashflow_service.get_cashflow_summary(start_date, end_date)

    assert summary["total_income"] == 0.0
    assert summary["total_expenses"] == 0.0
    assert summary["total_savings"] == 0.0
    assert summary["average_monthly_savings"] == 0.0
