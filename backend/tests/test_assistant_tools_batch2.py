"""Tests for Assistant tools Batch 2: spending_patterns, merchant_insights, goal_progress."""

from __future__ import annotations

from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.transaction import Transaction as TransactionModel
from backend.db.models.asset import Asset, AssetType
from backend.services.assistant_service import AssistantService


@pytest.fixture
def db() -> Session:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


@pytest.fixture
def assistant_service(db: Session) -> AssistantService:
    """Create AssistantService with mocked provider."""
    service = AssistantService(
        db=db,
        provider_type="ollama",
        ollama_host="http://localhost:11434",
        ollama_model="llama3.1:8b"
    )
    return service


@pytest.fixture
def sample_transactions(db: Session) -> list[TransactionModel]:
    """Create sample transactions for testing."""
    today = datetime.now()
    transactions = [
        # Current month groceries
        TransactionModel(
            type="expense",
            category="Groceries",
            merchant="Loblaws",
            description="Grocery shopping",
            amount=Decimal("-150.00"),
            currency="CAD",
            date=today - timedelta(days=5)
        ),
        TransactionModel(
            type="expense",
            category="Groceries",
            merchant="Costco",
            description="Weekly shopping",
            amount=Decimal("-200.00"),
            currency="CAD",
            date=today - timedelta(days=12)
        ),
        # Previous month groceries
        TransactionModel(
            type="expense",
            category="Groceries",
            merchant="Loblaws",
            description="Grocery shopping",
            amount=Decimal("-120.00"),
            currency="CAD",
            date=today - timedelta(days=35)
        ),
        # Gas transactions
        TransactionModel(
            type="expense",
            category="Gas",
            merchant="Shell",
            description="Gas fill-up",
            amount=Decimal("-60.00"),
            currency="CAD",
            date=today - timedelta(days=8)
        ),
        TransactionModel(
            type="expense",
            category="Gas",
            merchant="Esso",
            description="Gas fill-up",
            amount=Decimal("-55.00"),
            currency="CAD",
            date=today - timedelta(days=25)
        ),
        # Dining (anomaly - unusually high)
        TransactionModel(
            type="expense",
            category="Dining",
            merchant="Restaurant",
            description="Dinner",
            amount=Decimal("-150.00"),
            currency="CAD",
            date=today - timedelta(days=3)
        ),
        TransactionModel(
            type="expense",
            category="Dining",
            merchant="Cafe",
            description="Coffee",
            amount=Decimal("-15.00"),
            currency="CAD",
            date=today - timedelta(days=32)
        ),
        # Income
        TransactionModel(
            type="income",
            category="Salary",
            merchant="Employer",
            description="Monthly salary",
            amount=Decimal("5000.00"),
            currency="CAD",
            date=today - timedelta(days=2)
        ),
        # Merchant repeat transactions
        TransactionModel(
            type="expense",
            category="Groceries",
            merchant="Costco",
            description="Shopping",
            amount=Decimal("-180.00"),
            currency="CAD",
            date=today - timedelta(days=42)
        ),
    ]

    for tx in transactions:
        db.add(tx)
    db.commit()

    return transactions


def test_spending_patterns_calculates_trends(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test spending_patterns returns category trends."""
    result = assistant_service.spending_patterns(months=3)

    assert "top_categories" in result
    assert "anomalies" in result
    assert "total_spending" in result
    assert "average_monthly" in result
    assert result["analysis_months"] == 3

    # Should have top categories
    assert len(result["top_categories"]) > 0
    top_cat = result["top_categories"][0]
    assert "category" in top_cat
    assert "current_month" in top_cat
    assert "trend" in top_cat


def test_spending_patterns_detects_anomalies(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test spending_patterns detects high spending anomalies."""
    result = assistant_service.spending_patterns(months=3)

    # Dining had unusual spike (150 vs previous 15)
    anomalies = result["anomalies"]
    assert len(anomalies) > 0

    # Check for dining anomaly
    dining_anomaly = next((a for a in anomalies if a["category"] == "Dining"), None)
    if dining_anomaly:
        assert dining_anomaly["flag"] in ["unusual_high", "unusual_low"]
        assert dining_anomaly["percent_above_average"] > 0


def test_spending_patterns_with_zero_months(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test spending_patterns with edge case of 0 months."""
    result = assistant_service.spending_patterns(months=0)

    # Should still return valid structure
    assert "total_spending" in result
    assert result["analysis_months"] == 0
    assert "average_monthly" in result


def test_merchant_insights_lists_top_merchants(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test merchant_insights returns top merchants."""
    result = assistant_service.merchant_insights(months=3, top_n=10)

    assert "top_merchants" in result
    assert "total_unique_merchants" in result
    assert "total_merchant_spending" in result
    assert result["analysis_months"] == 3

    # Should have Costco and Loblaws
    merchants = {m["merchant"] for m in result["top_merchants"]}
    assert "Costco" in merchants or "Loblaws" in merchants


def test_merchant_insights_calculates_frequency(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test merchant_insights calculates transaction frequency."""
    result = assistant_service.merchant_insights(months=3, top_n=10)

    merchants = result["top_merchants"]
    for merchant in merchants:
        assert merchant["frequency"] in ["daily", "weekly", "monthly", "occasional"]
        assert merchant["transaction_count"] > 0
        assert merchant["average_transaction"] > 0


def test_merchant_insights_respects_top_n(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test merchant_insights respects top_n parameter."""
    result = assistant_service.merchant_insights(months=3, top_n=2)

    assert len(result["top_merchants"]) <= 2


def test_goal_progress_returns_net_worth(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test goal_progress returns net worth target."""
    result = assistant_service.goal_progress()

    assert "net_worth" in result
    assert "current" in result["net_worth"]
    assert "target" in result["net_worth"]
    assert "percent_complete" in result["net_worth"]
    assert result["net_worth"]["current"] >= 0


def test_goal_progress_returns_fire_timeline(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test goal_progress returns FIRE timeline."""
    result = assistant_service.goal_progress()

    if result["fire_timeline"]:
        fire = result["fire_timeline"]
        assert "current_portfolio" in fire
        assert "monthly_savings" in fire
        assert "assumed_annual_return" in fire
        # years_to_fire may be None if no savings


def test_goal_progress_overall_progress_logic(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test goal_progress overall_progress calculation."""
    result = assistant_service.goal_progress()

    assert result["overall_progress"] in ["on_track", "behind", "ahead"]
    # With income transactions, should be on_track
    assert result["overall_progress"] == "on_track"


def test_goal_progress_with_no_transactions(db: Session) -> None:
    """Test goal_progress with empty database."""
    service = AssistantService(db=db, provider_type="ollama")
    result = service.goal_progress()

    assert result["net_worth"]["current"] == 0
    assert result["overall_progress"] == "behind"


def test_spending_patterns_empty_database(db: Session) -> None:
    """Test spending_patterns with empty database."""
    service = AssistantService(db=db, provider_type="ollama")
    result = service.spending_patterns(months=3)

    assert result["total_spending"] == 0
    assert result["average_monthly"] == 0
    assert len(result["top_categories"]) == 0
    assert len(result["anomalies"]) == 0


def test_merchant_insights_empty_database(db: Session) -> None:
    """Test merchant_insights with empty database."""
    service = AssistantService(db=db, provider_type="ollama")
    result = service.merchant_insights(months=3, top_n=10)

    assert result["total_unique_merchants"] == 0
    assert result["total_merchant_spending"] == 0
    assert len(result["top_merchants"]) == 0


def test_execute_function_routes_correctly(assistant_service: AssistantService, sample_transactions: list) -> None:
    """Test execute_function routes to correct implementations."""
    # Test spending_patterns routing
    result = assistant_service.execute_function("spending_patterns", {"months": 3})
    assert "top_categories" in result

    # Test merchant_insights routing
    result = assistant_service.execute_function("merchant_insights", {"months": 3, "top_n": 5})
    assert "top_merchants" in result

    # Test goal_progress routing
    result = assistant_service.execute_function("goal_progress", {})
    assert "net_worth" in result


def test_execute_function_unknown_function(assistant_service: AssistantService) -> None:
    """Test execute_function raises error for unknown function."""
    with pytest.raises(ValueError, match="Unknown function"):
        assistant_service.execute_function("unknown_function", {})
