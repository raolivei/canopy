"""Unit tests for RecurringDetectionService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, Column, Integer, String, DateTime, DECIMAL
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from backend.services.recurring_detection_service import RecurringDetectionService

# Create minimal Transaction model for testing
Base = declarative_base()


class TestTransactionModel(Base):
    """Minimal transaction model for testing."""

    __tablename__ = "test_transactions"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    merchant = Column(String, nullable=True)
    amount = Column(DECIMAL(18, 2), nullable=False)
    category = Column(String, nullable=True)
    type = Column(String, default="expense")


@pytest.fixture
def test_db():
    """Create in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Monkey-patch to use TestTransactionModel
    import backend.services.recurring_detection_service as rds
    original_model = rds.TransactionModel
    rds.TransactionModel = TestTransactionModel

    yield session

    # Restore original
    rds.TransactionModel = original_model
    session.close()


@pytest.fixture
def netflix_monthly(test_db: Session):
    """Netflix subscription - 6 monthly charges."""
    today = date.today()
    txns = []

    for i in range(6):
        txn = TestTransactionModel(
            date=today - timedelta(days=150 - (i * 30)),
            merchant="Netflix",
            amount=Decimal("-15.99"),
            category="Entertainment",
            type="expense",
        )
        test_db.add(txn)
        txns.append(txn)

    test_db.commit()
    return txns


@pytest.fixture
def weekly_groceries(test_db: Session):
    """Weekly Loblaws groceries - 12 weeks, ~$150 ±5%."""
    today = date.today()
    txns = []
    amounts = [150.00, 147.50, 152.30, 148.00, 151.75, 149.20,
               150.50, 148.80, 152.00, 147.00, 151.00, 149.50]

    for i, amt in enumerate(amounts):
        txn = TestTransactionModel(
            date=today - timedelta(days=84 - (i * 7)),
            merchant="Loblaws",
            amount=Decimal(str(-amt)),
            category="Groceries",
            type="expense",
        )
        test_db.add(txn)
        txns.append(txn)

    test_db.commit()
    return txns


@pytest.fixture
def one_off_purchases(test_db: Session):
    """Random one-off purchases (should NOT be recurring)."""
    today = date.today()
    txns = [
        TestTransactionModel(
            date=today - timedelta(days=50),
            merchant="Best Buy",
            amount=Decimal("-499.99"),
            category="Electronics",
            type="expense",
        ),
        TestTransactionModel(
            date=today - timedelta(days=30),
            merchant="Home Depot",
            amount=Decimal("-87.43"),
            category="Home Improvement",
            type="expense",
        ),
    ]

    for txn in txns:
        test_db.add(txn)

    test_db.commit()
    return txns


class TestRecurringDetectionService:
    """Test RecurringDetectionService methods."""

    def test_detect_recurring_patterns_monthly(self, test_db: Session, netflix_monthly):
        """Detect monthly Netflix pattern."""
        service = RecurringDetectionService(test_db)
        patterns = service.detect_recurring_patterns(months=6)

        netflix_pattern = next((p for p in patterns if p.merchant == "Netflix"), None)

        assert netflix_pattern is not None
        assert netflix_pattern.frequency_days == 30
        assert netflix_pattern.avg_amount == 15.99
        assert netflix_pattern.occurrences >= 5  # May be 5-6 depending on date range
        assert netflix_pattern.confidence > 0.5
        assert netflix_pattern.category == "Entertainment"

    def test_detect_recurring_patterns_weekly(self, test_db: Session, weekly_groceries):
        """Detect weekly Loblaws pattern."""
        service = RecurringDetectionService(test_db)
        patterns = service.detect_recurring_patterns(months=3)

        loblaws_pattern = next((p for p in patterns if p.merchant == "Loblaws"), None)

        assert loblaws_pattern is not None
        assert loblaws_pattern.frequency_days == 7
        assert 149.0 <= loblaws_pattern.avg_amount <= 151.0
        assert loblaws_pattern.occurrences == 12
        assert loblaws_pattern.confidence > 0.7
        assert loblaws_pattern.category == "Groceries"

    def test_get_recurring_predictions(self, test_db: Session, netflix_monthly):
        """Predict upcoming Netflix charge."""
        service = RecurringDetectionService(test_db)
        predictions = service.get_recurring_predictions(next_days=30)

        netflix_pred = next((p for p in predictions if p.pattern.merchant == "Netflix"), None)

        assert netflix_pred is not None
        assert 0 <= netflix_pred.days_until_next <= 30
        assert netflix_pred.amount_range[0] == round(15.99 * 0.9, 2)
        assert netflix_pred.amount_range[1] == round(15.99 * 1.1, 2)

    def test_classify_transaction_recurring(self, test_db: Session, netflix_monthly):
        """Classify Netflix transaction as recurring."""
        service = RecurringDetectionService(test_db)

        # Use first Netflix transaction
        result = service.classify_transaction(netflix_monthly[0].id)

        assert result["is_recurring"] is True
        assert result["confidence"] > 0.5
        assert result["pattern"] is not None
        assert result["pattern"].merchant == "Netflix"

    def test_classify_transaction_not_recurring(self, test_db: Session, one_off_purchases):
        """Classify one-off purchase as not recurring."""
        service = RecurringDetectionService(test_db)

        result = service.classify_transaction(one_off_purchases[0].id)

        assert result["is_recurring"] is False
        assert result["confidence"] is None
        assert result["pattern"] is None

    def test_no_patterns_under_3_occurrences(self, test_db: Session):
        """Require minimum 3 occurrences."""
        today = date.today()

        # Only 2 transactions
        for i in range(2):
            txn = TestTransactionModel(
                date=today - timedelta(days=60 - (i * 30)),
                merchant="Spotify",
                amount=Decimal("-9.99"),
                category="Entertainment",
                type="expense",
            )
            test_db.add(txn)

        test_db.commit()

        service = RecurringDetectionService(test_db)
        patterns = service.detect_recurring_patterns(months=3)

        spotify_pattern = next((p for p in patterns if p.merchant == "Spotify"), None)
        assert spotify_pattern is None

    def test_amount_variance_edge_exactly_10_percent(self, test_db: Session):
        """Test exactly 10% variance edge case - amounts at ±10% from avg should pass."""
        today = date.today()

        # Amounts at exactly ±10% variance from avg (100)
        # avg = 100, each amount differs by exactly 10% from avg
        amounts = [90.00, 100.00, 110.00]

        for i, amt in enumerate(amounts):
            txn = TestTransactionModel(
                date=today - timedelta(days=90 - (i * 30)),
                merchant="Gym",
                amount=Decimal(str(-amt)),
                category="Fitness",
                type="expense",
            )
            test_db.add(txn)

        test_db.commit()

        service = RecurringDetectionService(test_db)
        patterns = service.detect_recurring_patterns(months=4)

        gym_pattern = next((p for p in patterns if p.merchant == "Gym"), None)
        # This should pass: 90 vs 100 = 10%, 110 vs 100 = 10%, both at threshold
        assert gym_pattern is not None
        assert gym_pattern.occurrences == 3
        assert 99.0 <= gym_pattern.avg_amount <= 101.0

    def test_mixed_frequencies(self, test_db: Session, netflix_monthly, weekly_groceries):
        """Detect both weekly and monthly patterns."""
        service = RecurringDetectionService(test_db)
        patterns = service.detect_recurring_patterns(months=6)

        netflix = next((p for p in patterns if p.merchant == "Netflix"), None)
        loblaws = next((p for p in patterns if p.merchant == "Loblaws"), None)

        assert netflix is not None
        assert loblaws is not None
        assert netflix.frequency_days == 30
        assert loblaws.frequency_days == 7

    def test_empty_database(self, test_db: Session):
        """Handle empty database gracefully."""
        service = RecurringDetectionService(test_db)

        patterns = service.detect_recurring_patterns(months=3)
        predictions = service.get_recurring_predictions(next_days=30)

        assert patterns == []
        assert predictions == []

    def test_patterns_sorted_by_confidence(self, test_db: Session, netflix_monthly, weekly_groceries):
        """Patterns sorted by confidence (highest first)."""
        service = RecurringDetectionService(test_db)
        patterns = service.detect_recurring_patterns(months=6)

        assert len(patterns) >= 2
        for i in range(len(patterns) - 1):
            assert patterns[i].confidence >= patterns[i + 1].confidence

    def test_predictions_sorted_by_days_until(self, test_db: Session, netflix_monthly, weekly_groceries):
        """Predictions sorted by days_until_next (soonest first)."""
        service = RecurringDetectionService(test_db)
        predictions = service.get_recurring_predictions(next_days=30)

        if len(predictions) >= 2:
            for i in range(len(predictions) - 1):
                assert predictions[i].days_until_next <= predictions[i + 1].days_until_next
