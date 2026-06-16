"""Unit tests for Golden Questions regression suite."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from backend.services.golden_questions import GoldenQuestionsService


def create_mock_transaction(
    date_val, merchant, description, amount, category, type_val
):
    """Create a mock transaction object."""
    tx = MagicMock()
    tx.date = (
        date_val
        if isinstance(date_val, datetime)
        else datetime.combine(date_val, datetime.min.time())
    )
    tx.merchant = merchant
    tx.description = description
    tx.amount = Decimal(str(amount))
    tx.category = category
    tx.type = type_val
    tx.currency = "CAD"
    return tx


def create_mock_asset(type_val, amount_cad):
    """Create a mock asset object."""
    asset = MagicMock()
    asset.type = type_val
    asset.amount_cad = Decimal(str(amount_cad))
    return asset


@pytest.fixture
def mock_db_with_data():
    """Create a mock database with realistic financial data."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Transactions
    txns = [
        # Income
        create_mock_transaction(
            month_start, "Employer", "Salary", "5000.00", "Income", "income"
        ),
        # Expenses
        create_mock_transaction(
            month_start + timedelta(days=1),
            "Supermarket",
            "Groceries",
            "-150.00",
            "Groceries",
            "expense",
        ),
        create_mock_transaction(
            month_start + timedelta(days=5),
            "Shell Gas",
            "Fuel",
            "-60.00",
            "Transportation",
            "expense",
        ),
        create_mock_transaction(
            month_start + timedelta(days=10),
            "Netflix",
            "Subscription",
            "-16.99",
            "Entertainment",
            "expense",
        ),
        create_mock_transaction(
            month_start + timedelta(days=15),
            "Supermarket",
            "Groceries",
            "-180.00",
            "Groceries",
            "expense",
        ),
        create_mock_transaction(
            month_start + timedelta(days=20),
            "Restaurant",
            "Dinner",
            "-95.00",
            "Dining",
            "expense",
        ),
    ]

    # Assets
    assets = [
        create_mock_asset("RRSP", 50000.00),
        create_mock_asset("TFSA", 30000.00),
        create_mock_asset("Chequing", 5000.00),
    ]

    # Mock database
    mock_db = MagicMock()

    def mock_execute(query):
        result = MagicMock()

        # Handle sum queries
        if hasattr(query, "_raw_columns"):
            # Crude check for sum aggregation
            if "sum" in str(query).lower():
                if "income" in str(query).lower():
                    result.scalar = MagicMock(return_value=5000.00)
                elif "expense" in str(query).lower():
                    result.scalar = MagicMock(return_value=-585.99)
                else:
                    result.scalar = MagicMock(return_value=85000.00)
            elif "group_by" in str(query).lower():
                # Group by queries return scalars().all()
                if "category" in str(query).lower():
                    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(
                        return_value=[
                            ("Groceries", -330.00),
                            ("Transportation", -60.00),
                            ("Entertainment", -16.99),
                        ]
                    )))
                elif "merchant" in str(query).lower():
                    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(
                        return_value=[
                            ("Supermarket", -330.00),
                            ("Shell Gas", -60.00),
                            ("Netflix", -16.99),
                        ]
                    )))
                elif "type" in str(query).lower() and "asset" in str(query).lower():
                    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(
                        return_value=[
                            ("RRSP", 50000.00),
                            ("TFSA", 30000.00),
                            ("Chequing", 5000.00),
                        ]
                    )))

        result.all = MagicMock(return_value=[])
        return result

    mock_db.execute = mock_execute
    return mock_db


class TestGoldenQuestionsService:
    """Test Golden Questions Service."""

    def test_net_worth_canopy(self, mock_db_with_data):
        """Test net worth calculation from Canopy."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._net_worth_canopy()
        assert isinstance(result, float)
        assert result >= 0

    def test_spending_this_month_canopy(self, mock_db_with_data):
        """Test monthly spending calculation."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._spending_this_month_canopy()
        assert isinstance(result, float)
        assert result >= 0

    def test_savings_rate_canopy(self, mock_db_with_data):
        """Test savings rate calculation."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._savings_rate_canopy()
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_top_categories_canopy(self, mock_db_with_data):
        """Test top spending categories."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._top_categories_canopy()
        assert isinstance(result, list)

    def test_top_merchants_canopy(self, mock_db_with_data):
        """Test top merchants calculation."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._top_merchants_canopy()
        assert isinstance(result, list)

    def test_asset_allocation_canopy(self, mock_db_with_data):
        """Test asset allocation."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._asset_allocation_canopy()
        assert isinstance(result, dict)
        total_pct = sum(result.values())
        assert 0 <= total_pct <= 100

    def test_fire_goal_canopy(self, mock_db_with_data):
        """Test FIRE goal progress."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._fire_goal_canopy()
        assert isinstance(result, str)
        assert "Current net worth" in result

    def test_anomalies_canopy(self, mock_db_with_data):
        """Test anomaly detection."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._anomalies_canopy()
        assert isinstance(result, list)

    def test_budget_overages_canopy(self, mock_db_with_data):
        """Test budget overages."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._budget_overages_canopy()
        assert isinstance(result, list)

    def test_next_subscription_canopy(self, mock_db_with_data):
        """Test subscription detection."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._next_subscription_canopy()
        assert result is None or isinstance(result, str)

    def test_compare_numeric_exact(self, mock_db_with_data):
        """Test numeric comparison with exact match."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._compare_numeric(100.0, 100.0, "test")
        assert result["match_type"] == "exact"
        assert result["passed"]
        assert result["confidence"] == 1.0
        assert result["numerical_delta"] == 0.0

    def test_compare_numeric_small_delta(self, mock_db_with_data):
        """Test numeric comparison with small delta."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._compare_numeric(100.0, 100.50, "test")
        assert result["match_type"] == "numerical_delta"
        assert result["passed"]
        assert result["delta_percent"] < 1

    def test_compare_numeric_large_delta(self, mock_db_with_data):
        """Test numeric comparison with large delta."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._compare_numeric(100.0, 150.0, "test")
        assert result["match_type"] == "numerical_delta"
        assert not result["passed"]
        assert result["delta_percent"] > 1

    def test_compare_categorical_exact(self, mock_db_with_data):
        """Test categorical comparison with exact match."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service._compare_categorical("Groceries", "Groceries", "test")
        assert result["match_type"] == "exact"
        assert result["passed"]
        assert result["confidence"] == 1.0

    def test_compare_categorical_list_partial(self, mock_db_with_data):
        """Test categorical comparison with list overlap."""
        service = GoldenQuestionsService(mock_db_with_data)
        canopy = ["Groceries", "Transportation", "Entertainment"]
        monarch = ["Groceries", "Transportation", "Dining"]
        result = service._compare_categorical(canopy, monarch, "test")
        assert result["confidence"] >= 0.5

    def test_run_golden_questions(self, mock_db_with_data):
        """Test running all 10 golden questions."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service.run_golden_questions(verbose=False)

        assert "run_id" in result
        assert result["total_questions"] == 10
        assert result["passed"] + result["failed"] == result["total_questions"]
        assert 0 <= result["pass_rate"] <= 1
        assert len(result["results"]) == 10
        assert result["execution_time_ms"] >= 0

    def test_run_golden_questions_verbose(self, mock_db_with_data):
        """Test running golden questions with verbose output."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service.run_golden_questions(verbose=True)

        assert result["total_questions"] == 10
        assert "timestamp" in result
        assert isinstance(result["results"], list)

    def test_run_golden_questions_stop_on_failure(self, mock_db_with_data):
        """Test stop on first failure option."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service.run_golden_questions(stop_on_failure=True)

        # Should have at least some results
        assert len(result["results"]) > 0

    def test_golden_question_result_structure(self, mock_db_with_data):
        """Test structure of individual golden question results."""
        service = GoldenQuestionsService(mock_db_with_data)
        result = service.run_golden_questions()

        for res in result["results"]:
            assert "question_number" in res
            assert "question" in res
            assert "category" in res
            assert "canopy_answer" in res
            assert "monarch_reference" in res
            assert "match_type" in res
            assert "confidence" in res
            assert "passed" in res
            assert 1 <= res["question_number"] <= 10
            assert 0 <= res["confidence"] <= 1
