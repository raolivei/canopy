"""Unit tests for AssistantService tools: budget_status, cashflow_summary, recurring_analysis."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from backend.services.assistant_service import AssistantService


def create_mock_transaction(date_val, merchant, description, amount, category, type_val):
    """Create a mock transaction object."""
    tx = MagicMock()
    tx.date = date_val if isinstance(date_val, datetime) else datetime.combine(date_val, datetime.min.time())
    tx.merchant = merchant
    tx.description = description
    tx.amount = Decimal(str(amount))
    tx.category = category
    tx.type = type_val
    tx.currency = "CAD"
    return tx


@pytest.fixture
def mock_db_for_budget():
    """Create a mock database session for budget testing."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    txns = [
        create_mock_transaction(month_start, "Supermarket", "Groceries", "-150.00", "Groceries", "expense"),
        create_mock_transaction(month_start + timedelta(days=5), "Gas Station", "Fuel", "-60.00", "Transportation", "expense"),
        create_mock_transaction(month_start + timedelta(days=10), "Supermarket", "Groceries", "-180.00", "Groceries", "expense"),
        create_mock_transaction(month_start + timedelta(days=15), "Restaurant", "Dinner", "-95.00", "Dining Out", "expense"),
        create_mock_transaction(month_start + timedelta(days=20), "Employer", "Salary", "5000.00", "Income", "income"),
    ]

    mock_db = MagicMock()
    mock_db.execute = MagicMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=txns)))))
    return mock_db, txns


@pytest.fixture
def mock_db_for_recurring():
    """Create a mock database session for recurring transaction analysis."""
    today = date.today()
    three_months_ago = today - timedelta(days=90)

    txns = [
        # Monthly subscription (Netflix-like)
        create_mock_transaction(three_months_ago, "Netflix", "Monthly subscription", "-16.99", "Entertainment", "expense"),
        create_mock_transaction(three_months_ago + timedelta(days=30), "Netflix", "Monthly subscription", "-16.99", "Entertainment", "expense"),
        create_mock_transaction(three_months_ago + timedelta(days=60), "Netflix", "Monthly subscription", "-16.99", "Entertainment", "expense"),
        # Weekly coffee
        create_mock_transaction(three_months_ago + timedelta(days=7), "Coffee Shop", "Coffee", "-5.50", "Dining Out", "expense"),
        create_mock_transaction(three_months_ago + timedelta(days=14), "Coffee Shop", "Coffee", "-5.75", "Dining Out", "expense"),
        create_mock_transaction(three_months_ago + timedelta(days=21), "Coffee Shop", "Coffee", "-5.50", "Dining Out", "expense"),
        create_mock_transaction(three_months_ago + timedelta(days=28), "Coffee Shop", "Coffee", "-6.00", "Dining Out", "expense"),
        # One-off transaction
        create_mock_transaction(three_months_ago + timedelta(days=10), "Random Store", "One-time purchase", "-50.00", "Shopping", "expense"),
    ]

    mock_db = MagicMock()
    mock_db.execute = MagicMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=txns)))))
    return mock_db, txns


class TestAssistantServiceTools:
    """Test AssistantService tools."""

    def test_budget_status_current_month(self, mock_db_for_budget):
        """Test budget_status returns current month data."""
        mock_db, txns = mock_db_for_budget
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.budget_status()

        assert result["currency"] == "CAD"
        assert result["total_spent"] > 0
        assert "month" in result
        assert "alerts" in result
        assert "month_progress_percent" in result

    def test_budget_status_specific_month(self, mock_db_for_budget):
        """Test budget_status with specific month parameter."""
        mock_db, _ = mock_db_for_budget
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        today = date.today()
        month_str = f"{today.year}-{today.month:02d}"

        result = service.budget_status(month=month_str)

        assert result["month"] == month_str
        assert result["total_spent"] == pytest.approx(485.00, abs=0.01)

    def test_budget_status_alerts(self, mock_db_for_budget):
        """Test budget_status generates alerts for overspending."""
        mock_db, _ = mock_db_for_budget
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.budget_status()

        for alert in result["alerts"]:
            assert "category" in alert
            assert "spent" in alert
            assert alert["status"] in ["on_track", "warning", "critical"]

    def test_cashflow_summary_current_month(self, mock_db_for_budget):
        """Test cashflow_summary returns current month data."""
        mock_db, _ = mock_db_for_budget
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.cashflow_summary()

        assert result["currency"] == "CAD"
        assert result["total_income"] == pytest.approx(5000.00, abs=0.01)
        assert result["total_expenses"] == pytest.approx(485.00, abs=0.01)
        assert result["net_savings"] == pytest.approx(4515.00, abs=0.01)

    def test_cashflow_summary_breakdown(self, mock_db_for_budget):
        """Test cashflow_summary includes expense breakdown."""
        mock_db, _ = mock_db_for_budget
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.cashflow_summary()

        assert "expense_breakdown" in result
        assert "Groceries" in result["expense_breakdown"]

    def test_cashflow_summary_trends(self, mock_db_for_budget):
        """Test cashflow_summary includes trend information."""
        mock_db, _ = mock_db_for_budget
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.cashflow_summary()

        assert result["income_trend"] in ["up", "down", "stable"]
        assert result["expense_trend"] in ["up", "down", "stable"]

    def test_recurring_analysis_detects_monthly(self, mock_db_for_recurring):
        """Test recurring_analysis detects monthly subscriptions."""
        mock_db, _ = mock_db_for_recurring
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.recurring_analysis(months=3)

        assert result["currency"] == "CAD"
        assert result["recurring_count"] > 0

        netflix = next((t for t in result["transactions"] if "Netflix" in t["merchant"]), None)
        assert netflix is not None
        assert netflix["frequency"] == "monthly"

    def test_recurring_analysis_detects_weekly(self, mock_db_for_recurring):
        """Test recurring_analysis detects weekly patterns."""
        mock_db, _ = mock_db_for_recurring
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.recurring_analysis(months=3)

        coffee = next((t for t in result["transactions"] if "Coffee" in t["merchant"]), None)
        assert coffee is not None
        assert coffee["frequency"] == "weekly"

    def test_recurring_analysis_next_date(self, mock_db_for_recurring):
        """Test recurring_analysis calculates next payment dates."""
        mock_db, _ = mock_db_for_recurring
        service = AssistantService.__new__(AssistantService)
        service.db = mock_db

        result = service.recurring_analysis(months=3)

        for txn in result["transactions"]:
            assert "next_date" in txn
            assert isinstance(txn["next_date"], str)
            assert len(txn["next_date"]) > 0
