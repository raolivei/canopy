"""Tests for AssistantService high-value tools.

Canopy - Personal Finance Platform
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.base import Base
from backend.db.models.asset import Asset, AssetType
from backend.db.models.budget import Budget, BudgetCategory, BudgetTracking, PeriodType
from backend.db.models.transaction import Transaction, TransactionType
from backend.services.assistant_service import AssistantService


@pytest.fixture
def db():
    """Create in-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def assistant_service(db):
    """Create AssistantService instance."""
    return AssistantService(
        db=db,
        provider_type="ollama",
        ollama_host="http://localhost:11434",
        ollama_model="llama3.1:8b"
    )


@pytest.fixture
def sample_transactions(db):
    """Create sample transactions."""
    now = datetime.utcnow()

    transactions = [
        Transaction(
            description="Costco Gas",
            amount=Decimal("-45.50"),
            currency="CAD",
            type=TransactionType.EXPENSE,
            date=now - timedelta(days=5),
            category="Gas",
            merchant="Costco"
        ),
        Transaction(
            description="Loblaws Groceries",
            amount=Decimal("-120.00"),
            currency="CAD",
            type=TransactionType.EXPENSE,
            date=now - timedelta(days=3),
            category="Groceries",
            merchant="Loblaws"
        ),
        Transaction(
            description="Netflix Subscription",
            amount=Decimal("-16.99"),
            currency="CAD",
            type=TransactionType.EXPENSE,
            date=now - timedelta(days=2),
            category="Entertainment",
            merchant="Netflix"
        ),
        Transaction(
            description="Salary",
            amount=Decimal("3500.00"),
            currency="CAD",
            type=TransactionType.INCOME,
            date=now - timedelta(days=1),
            category="Income",
            merchant="Employer"
        ),
        Transaction(
            description="Costco Gas",
            amount=Decimal("-42.00"),
            currency="CAD",
            type=TransactionType.EXPENSE,
            date=now - timedelta(days=35),
            category="Gas",
            merchant="Costco"
        ),
        Transaction(
            description="Netflix Subscription",
            amount=Decimal("-16.99"),
            currency="CAD",
            type=TransactionType.EXPENSE,
            date=now - timedelta(days=32),
            category="Entertainment",
            merchant="Netflix"
        ),
    ]

    for tx in transactions:
        db.add(tx)
    db.commit()

    return transactions


@pytest.fixture
def sample_assets(db):
    """Create sample assets."""
    assets = [
        Asset(
            symbol="CHEQUING",
            name="RBC Chequing",
            asset_type=AssetType.BANK_CHECKING,
            currency="CAD",
            institution="RBC",
            current_price=Decimal("5000.00"),
            price_updated_at=datetime.utcnow()
        ),
        Asset(
            symbol="TFSA",
            name="RBC TFSA",
            asset_type=AssetType.RETIREMENT_TFSA,
            currency="CAD",
            institution="RBC",
            current_price=Decimal("25000.00"),
            price_updated_at=datetime.utcnow()
        ),
        Asset(
            symbol="CC_VISA",
            name="RBC Visa",
            asset_type=AssetType.LIABILITY_CREDIT_CARD,
            currency="CAD",
            institution="RBC",
            is_liability=True,
            current_price=Decimal("-1200.00"),
            price_updated_at=datetime.utcnow()
        ),
    ]

    for asset in assets:
        db.add(asset)
    db.commit()

    return assets


@pytest.fixture
def sample_budget(db):
    """Create sample budget."""
    budget = Budget(
        name="Monthly Budget",
        currency="CAD",
        is_active=True
    )
    db.add(budget)
    db.flush()

    categories = [
        BudgetCategory(
            budget_id=budget.id,
            category_name="Groceries",
            limit_amount=Decimal("500.00"),
            period_type=PeriodType.MONTHLY
        ),
        BudgetCategory(
            budget_id=budget.id,
            category_name="Gas",
            limit_amount=Decimal("200.00"),
            period_type=PeriodType.MONTHLY
        ),
    ]

    for cat in categories:
        db.add(cat)
    db.commit()

    return budget


class TestGetAccounts:
    """Tests for get_accounts tool."""

    def test_get_accounts_returns_all_accounts(self, assistant_service, sample_assets):
        """Should return all accounts with balances."""
        result = assistant_service.get_accounts()

        assert len(result) == 3
        assert all("name" in acc for acc in result)
        assert all("balance" in acc for acc in result)
        assert all("type" in acc for acc in result)

    def test_get_accounts_includes_institution(self, assistant_service, sample_assets):
        """Should include institution information."""
        result = assistant_service.get_accounts()

        rbc_accounts = [a for a in result if a["institution"] == "RBC"]
        assert len(rbc_accounts) == 3

    def test_get_accounts_empty_when_no_assets(self, assistant_service, db):
        """Should return empty list when no assets."""
        result = assistant_service.get_accounts()
        assert result == []


class TestGetBudgetStatus:
    """Tests for get_budget_status tool."""

    def test_get_budget_status_current_month(self, assistant_service, sample_budget, sample_transactions):
        """Should return budget status for current month."""
        result = assistant_service.get_budget_status()

        assert "month" in result
        assert "budget_limit" in result
        assert "actual_spent" in result
        assert "categories" in result

    def test_get_budget_status_with_specific_month(self, assistant_service, sample_budget, sample_transactions):
        """Should accept specific month parameter."""
        result = assistant_service.get_budget_status(month="2024-01")

        assert result["month"] == "2024-01"

    def test_get_budget_status_invalid_format(self, assistant_service):
        """Should handle invalid month format."""
        result = assistant_service.get_budget_status(month="invalid")

        assert "error" in result

    def test_get_budget_status_no_budget(self, assistant_service, db):
        """Should handle case with no budget."""
        result = assistant_service.get_budget_status()

        assert "message" in result
        assert result["budget_limit"] == 0


class TestGetRecurringSummary:
    """Tests for get_recurring_summary tool."""

    def test_get_recurring_summary_returns_patterns(self, assistant_service, sample_transactions):
        """Should detect recurring transactions."""
        result = assistant_service.get_recurring_summary()

        assert isinstance(result, list)

    def test_get_recurring_summary_structure(self, assistant_service, sample_transactions):
        """Should return correct structure for patterns."""
        result = assistant_service.get_recurring_summary()

        if result:
            pattern = result[0]
            assert "merchant" in pattern
            assert "frequency" in pattern
            assert "confidence" in pattern
            assert "currency" in pattern

    def test_get_recurring_summary_custom_lookback(self, assistant_service, sample_transactions):
        """Should accept custom lookback period."""
        result = assistant_service.get_recurring_summary(lookback_months=6)
        assert isinstance(result, list)


class TestGetCashflowAnalysis:
    """Tests for get_cashflow_analysis tool."""

    def test_get_cashflow_analysis_returns_monthly_data(self, assistant_service, sample_transactions):
        """Should return monthly cashflow data."""
        result = assistant_service.get_cashflow_analysis()

        assert "monthly_data" in result
        assert "trend" in result
        assert "average_monthly_income" in result
        assert "average_monthly_expenses" in result

    def test_get_cashflow_analysis_structure(self, assistant_service, sample_transactions):
        """Should return correct structure."""
        result = assistant_service.get_cashflow_analysis(months=3)

        assert result["trend"] in ["up", "down", "stable"]
        assert result["currency"] == "CAD"
        assert isinstance(result["monthly_data"], list)

    def test_get_cashflow_analysis_monthly_items(self, assistant_service, sample_transactions):
        """Monthly items should have all required fields."""
        result = assistant_service.get_cashflow_analysis()

        if result["monthly_data"]:
            month = result["monthly_data"][0]
            assert "month" in month
            assert "income" in month
            assert "expenses" in month
            assert "savings" in month
            assert "savings_rate" in month


class TestAnalyzeSpendingPatterns:
    """Tests for analyze_spending_patterns tool."""

    def test_analyze_spending_patterns_returns_structure(self, assistant_service, sample_transactions):
        """Should return spending analysis structure."""
        result = assistant_service.analyze_spending_patterns()

        assert "top_merchants" in result
        assert "top_categories" in result
        assert "total_spending" in result
        assert "transaction_count" in result

    def test_analyze_spending_patterns_top_merchants(self, assistant_service, sample_transactions):
        """Should identify top merchants."""
        result = assistant_service.analyze_spending_patterns(months=12)

        merchants = result["top_merchants"]
        assert len(merchants) > 0
        if merchants:
            assert "name" in merchants[0]
            assert "total" in merchants[0]

    def test_analyze_spending_patterns_top_categories(self, assistant_service, sample_transactions):
        """Should identify top categories."""
        result = assistant_service.analyze_spending_patterns()

        categories = result["top_categories"]
        assert len(categories) > 0
        if categories:
            assert "name" in categories[0]
            assert "total" in categories[0]

    def test_analyze_spending_patterns_trends(self, assistant_service, sample_transactions):
        """Should include trend analysis."""
        result = assistant_service.analyze_spending_patterns()

        if result["trends"]:
            trend = result["trends"][0]
            assert "period" in trend
            assert "direction" in trend


class TestGetMerchantInsights:
    """Tests for get_merchant_insights tool."""

    def test_get_merchant_insights_found(self, assistant_service, sample_transactions):
        """Should return insights for known merchant."""
        result = assistant_service.get_merchant_insights("Costco")

        assert result["merchant"] == "Costco"
        assert result["transaction_count"] > 0
        assert result["total_spent"] > 0

    def test_get_merchant_insights_structure(self, assistant_service, sample_transactions):
        """Should return complete insight structure."""
        result = assistant_service.get_merchant_insights("Netflix")

        assert "merchant" in result
        assert "total_spent" in result
        assert "transaction_count" in result
        assert "average_amount" in result
        assert "last_transaction" in result
        assert "frequency_per_month" in result

    def test_get_merchant_insights_not_found(self, assistant_service, sample_transactions):
        """Should handle merchant not found."""
        result = assistant_service.get_merchant_insights("UnknownStore")

        assert result["transaction_count"] == 0
        assert "message" in result

    def test_get_merchant_insights_custom_period(self, assistant_service, sample_transactions):
        """Should accept custom lookback period."""
        result = assistant_service.get_merchant_insights("Costco", months=1)

        assert isinstance(result, dict)


class TestExecuteFunction:
    """Tests for execute_function routing."""

    def test_execute_function_get_accounts(self, assistant_service, sample_assets):
        """Should route get_accounts correctly."""
        result = assistant_service.execute_function("get_accounts", {})
        assert isinstance(result, list)

    def test_execute_function_get_budget_status(self, assistant_service, sample_budget):
        """Should route get_budget_status correctly."""
        result = assistant_service.execute_function("get_budget_status", {})
        assert isinstance(result, dict)

    def test_execute_function_get_recurring_summary(self, assistant_service, sample_transactions):
        """Should route get_recurring_summary correctly."""
        result = assistant_service.execute_function("get_recurring_summary", {})
        assert isinstance(result, list)

    def test_execute_function_get_cashflow_analysis(self, assistant_service, sample_transactions):
        """Should route get_cashflow_analysis correctly."""
        result = assistant_service.execute_function("get_cashflow_analysis", {})
        assert isinstance(result, dict)

    def test_execute_function_analyze_spending_patterns(self, assistant_service, sample_transactions):
        """Should route analyze_spending_patterns correctly."""
        result = assistant_service.execute_function("analyze_spending_patterns", {})
        assert isinstance(result, dict)

    def test_execute_function_get_merchant_insights(self, assistant_service, sample_transactions):
        """Should route get_merchant_insights correctly."""
        result = assistant_service.execute_function(
            "get_merchant_insights",
            {"merchant_name": "Costco"}
        )
        assert isinstance(result, dict)

    def test_execute_function_unknown(self, assistant_service):
        """Should raise error for unknown function."""
        with pytest.raises(ValueError):
            assistant_service.execute_function("unknown_function", {})
