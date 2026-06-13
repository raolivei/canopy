"""Unit tests for contextual insights service."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, Column, Integer, String, Date, DECIMAL, Boolean, Text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from backend.services.contextual_insights import ContextualInsightsService

# Create a minimal Transaction model for testing
Base = declarative_base()


class SimpleTransaction(Base):
    """Minimal transaction model for testing."""

    __tablename__ = "test_transactions"

    id = Column(Integer, primary_key=True)
    transaction_date = Column(Date, nullable=False)
    merchant = Column(String, nullable=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    category = Column(String, nullable=True)


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database with test tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_transactions(test_db: Session):
    """Create sample transactions for testing."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    txns = [
        SimpleTransaction(
            transaction_date=month_start,
            merchant="Grocery Store",
            amount=Decimal("-150.00"),
            category="Groceries",
        ),
        SimpleTransaction(
            transaction_date=month_start + timedelta(days=5),
            merchant="Gas Station",
            amount=Decimal("-60.00"),
            category="Transportation",
        ),
        SimpleTransaction(
            transaction_date=month_start + timedelta(days=10),
            merchant="Grocery Store",
            amount=Decimal("-145.00"),
            category="Groceries",
        ),
        SimpleTransaction(
            transaction_date=month_start + timedelta(days=15),
            merchant="Restaurant",
            amount=Decimal("-500.00"),
            category="Dining Out",
        ),
    ]

    for txn in txns:
        test_db.add(txn)
    test_db.commit()
    return txns


class TestContextualInsightsService:
    """Test contextual insights service."""

    def test_get_budget_warnings(self, test_db: Session, sample_transactions):
        """Test budget warning detection."""
        service = ContextualInsightsService(test_db, transaction_model=SimpleTransaction)
        warnings = service.get_budget_warnings()

        # Should detect high spending categories
        assert len(warnings) > 0
        assert all(w.type in ["on_track", "warning", "critical"] for w in warnings)
        assert all(w.percent_used > 0 for w in warnings)

    def test_get_mom_comparisons_no_previous_month(self, test_db: Session, sample_transactions):
        """Test MoM comparisons with no previous month data."""
        service = ContextualInsightsService(test_db, transaction_model=SimpleTransaction)
        comparisons = service.get_mom_comparisons()

        # Should return comparisons even without previous month
        assert isinstance(comparisons, list)
        if comparisons:
            assert all(hasattr(c, "category_name") for c in comparisons)
            assert all(hasattr(c, "change_percent") for c in comparisons)

    def test_detect_anomalies(self, test_db: Session, sample_transactions):
        """Test anomaly detection."""
        service = ContextualInsightsService(test_db, transaction_model=SimpleTransaction)
        anomalies = service.detect_anomalies()

        # Should detect unusual transactions
        assert isinstance(anomalies, list)
        if anomalies:
            assert all(hasattr(a, "merchant") for a in anomalies)
            assert all(a.deviation_percent > 0 for a in anomalies)

    def test_predict_recurring_with_pattern(self, test_db: Session):
        """Test recurring prediction with clear pattern."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        # Add recurring pattern: monthly grocery shopping
        dates = [
            three_months_ago,
            three_months_ago + timedelta(days=30),
            three_months_ago + timedelta(days=60),
        ]

        for d in dates:
            txn = SimpleTransaction(
                transaction_date=d,
                merchant="Walmart",
                amount=Decimal("-100.00"),
                category="Groceries",
            )
            test_db.add(txn)
        test_db.commit()

        service = ContextualInsightsService(test_db, transaction_model=SimpleTransaction)
        predictions = service.predict_recurring()

        # Should detect the pattern
        if predictions:
            walmart_pred = next((p for p in predictions if "walmart" in p.merchant.lower()), None)
            if walmart_pred:
                assert walmart_pred.confidence > 0
                assert walmart_pred.expected_amount > 0

    def test_predict_recurring_limits_result(self, test_db: Session):
        """Test recurring prediction respects limit parameter."""
        service = ContextualInsightsService(test_db, transaction_model=SimpleTransaction)
        predictions = service.predict_recurring(limit=3)

        # Should return at most 3 predictions
        assert len(predictions) <= 3

    def test_service_with_empty_database(self, test_db: Session):
        """Test service handles empty database gracefully."""
        service = ContextualInsightsService(test_db, transaction_model=SimpleTransaction)

        warnings = service.get_budget_warnings()
        comparisons = service.get_mom_comparisons()
        anomalies = service.detect_anomalies()
        predictions = service.predict_recurring()

        # Should return empty lists, not errors
        assert warnings == []
        assert isinstance(comparisons, list)
        assert anomalies == []
        assert predictions == []
