"""Recurring transaction detection service.

Canopy - Personal Finance Platform

Provides:
- Pattern detection for recurring transactions (subscriptions, salary, etc.)
- Confidence scoring based on consistency and frequency
- Prediction of next occurrence
- Persistence of user-approved patterns
- Edge case handling (seasonal variations, one-offs)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from statistics import mean, stdev
from typing import Optional

from sqlalchemy.orm import Session


class Frequency(str, Enum):
    """Recurring transaction frequency."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


@dataclass
class RecurringPattern:
    """Detected or stored recurring transaction pattern."""

    id: Optional[int] = None  # Database ID for stored patterns
    merchant: str = ""
    category: Optional[str] = None
    average_amount: Decimal = Decimal("0")
    amount_variance: Decimal = Decimal("0")  # ±tolerance (absolute)
    frequency: Frequency = Frequency.MONTHLY
    next_expected: Optional[datetime] = None
    confidence: int = 0  # 0-100 score
    occurrences: list[datetime] = field(default_factory=list)  # Detected transaction dates
    should_skip_dates: list[datetime] = field(default_factory=list)  # Known delays/skips

    def to_dict(self) -> dict:
        """Convert pattern to dictionary for API serialization."""
        return {
            "id": self.id,
            "merchant": self.merchant,
            "category": self.category,
            "average_amount": float(self.average_amount),
            "amount_variance": float(self.amount_variance),
            "frequency": self.frequency.value,
            "next_expected": self.next_expected.isoformat() if self.next_expected else None,
            "confidence": self.confidence,
            "occurrences": [d.isoformat() for d in self.occurrences],
            "should_skip_dates": [d.isoformat() for d in self.should_skip_dates],
        }


class RecurringService:
    """Service for detecting and managing recurring transactions."""

    # Minimum occurrences to consider a pattern (confidence factor)
    MIN_OCCURRENCES = 2

    # Amount variance thresholds: allow variance up to this % of average
    AMOUNT_VARIANCE_PCT = 0.10  # 10%

    # Frequency detection windows (in days, with tolerance)
    FREQUENCY_WINDOWS = {
        Frequency.WEEKLY: (7, 1),  # 7 days ±1
        Frequency.BIWEEKLY: (14, 2),  # 14 days ±2
        Frequency.MONTHLY: (30, 3),  # 30 days ±3
        Frequency.QUARTERLY: (90, 5),  # 90 days ±5
        Frequency.ANNUAL: (365, 10),  # 365 days ±10
    }

    # Minimum confidence score for returning patterns
    MIN_CONFIDENCE = 70

    def __init__(self, db: Session):
        self.db = db

    def detect_recurring_transactions(
        self,
        lookback_months: int = 12,
    ) -> list[RecurringPattern]:
        """Detect recurring transaction patterns in transaction history.

        Groups transactions by (merchant, category, approximate_amount), analyzes
        frequency and consistency, and returns patterns with confidence > MIN_CONFIDENCE.

        Args:
            lookback_months: Number of months to analyze (default 12)

        Returns:
            List of detected RecurringPattern objects with confidence > 70%
        """
        from backend.db.models.transaction import Transaction, TransactionType

        # Calculate lookback window
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_months * 30)

        # Fetch recent transactions (exclude transfers)
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.date >= cutoff_date,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            )
            .order_by(Transaction.date.asc())
            .all()
        )

        if not transactions:
            return []

        # Group by (merchant, category)
        groups: dict[tuple[str, Optional[str]], list] = defaultdict(list)
        for txn in transactions:
            # Use merchant if available, otherwise description
            key_merchant = (txn.merchant or txn.description).lower().strip()
            key_category = (txn.category or "uncategorized").lower().strip()
            groups[(key_merchant, key_category)].append(txn)

        # Detect patterns from groups
        patterns: list[RecurringPattern] = []
        for (merchant, category), txns in groups.items():
            if len(txns) < self.MIN_OCCURRENCES:
                continue

            # Analyze this group for recurring patterns
            pattern = self._analyze_group(merchant, category, txns)
            if pattern and pattern.confidence >= self.MIN_CONFIDENCE:
                patterns.append(pattern)

        # Sort by confidence descending
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns

    def _analyze_group(
        self,
        merchant: str,
        category: Optional[str],
        transactions: list,
    ) -> Optional[RecurringPattern]:
        """Analyze a group of transactions for recurring patterns.

        Returns a RecurringPattern if a pattern is detected with sufficient confidence.
        """
        if len(transactions) < self.MIN_OCCURRENCES:
            return None

        # Extract amounts and dates
        amounts = [abs(float(txn.amount)) for txn in transactions]
        dates = [txn.date for txn in transactions]

        # Calculate amount statistics
        avg_amount = Decimal(str(mean(amounts)))
        amount_variance = self._calculate_amount_variance(amounts)

        # Detect frequency and calculate confidence
        frequency, confidence, intervals = self._detect_frequency(dates)
        if frequency is None or confidence < self.MIN_CONFIDENCE:
            return None

        # Predict next occurrence
        next_expected = self._predict_next_occurrence(dates, frequency, intervals)

        # Detect known skips or delays
        skip_dates = self._detect_anomalies(dates, frequency)

        return RecurringPattern(
            merchant=merchant,
            category=category,
            average_amount=avg_amount,
            amount_variance=amount_variance,
            frequency=frequency,
            next_expected=next_expected,
            confidence=confidence,
            occurrences=dates,
            should_skip_dates=skip_dates,
        )

    def _calculate_amount_variance(self, amounts: list[float]) -> Decimal:
        """Calculate the variance tolerance for amounts (±).

        Returns the standard deviation or variance threshold.
        """
        if len(amounts) < 2:
            return Decimal("0")

        try:
            std_dev = stdev(amounts)
            # Return variance as a percentage of mean, but cap at 10%
            mean_amount = mean(amounts)
            if mean_amount > 0:
                variance_pct = (std_dev / mean_amount) * 100
                variance_pct = min(variance_pct, self.AMOUNT_VARIANCE_PCT * 100)
                return Decimal(str(variance_pct))
        except Exception:
            pass

        return Decimal(str(self.AMOUNT_VARIANCE_PCT * 100))

    def _detect_frequency(
        self,
        dates: list[datetime],
    ) -> tuple[Optional[Frequency], int, list[int]]:
        """Detect frequency and calculate confidence.

        Analyzes intervals between transactions to determine frequency.
        Returns (Frequency, confidence_score, intervals_in_days).
        """
        if len(dates) < self.MIN_OCCURRENCES:
            return None, 0, []

        # Sort dates
        sorted_dates = sorted(dates)

        # Calculate intervals between consecutive transactions
        intervals = []
        for i in range(1, len(sorted_dates)):
            delta = (sorted_dates[i] - sorted_dates[i - 1]).days
            if delta > 0:  # Ignore same-day duplicates
                intervals.append(delta)

        if not intervals:
            return None, 0, []

        # Try to match intervals to known frequencies
        best_match = None
        best_confidence = 0
        best_intervals = intervals

        for freq, (window, tolerance) in self.FREQUENCY_WINDOWS.items():
            match_confidence = self._score_frequency_match(intervals, window, tolerance)
            if match_confidence > best_confidence:
                best_match = freq
                best_confidence = match_confidence
                best_intervals = intervals

        if best_match is None or best_confidence < self.MIN_CONFIDENCE:
            return None, 0, intervals

        return best_match, best_confidence, best_intervals

    def _score_frequency_match(
        self,
        intervals: list[int],
        expected_window: int,
        tolerance: int,
    ) -> int:
        """Score how well intervals match expected frequency.

        Returns confidence 0-100.
        """
        if not intervals:
            return 0

        # Check how many intervals fall within the window
        in_window = sum(
            1 for i in intervals
            if expected_window - tolerance <= i <= expected_window + tolerance
        )
        match_rate = in_window / len(intervals)

        # Score based on match rate and consistency
        score = int(match_rate * 100)

        # Bonus for consistent (low variance) intervals
        if len(intervals) >= 3:
            try:
                std_dev = stdev(intervals)
                mean_interval = sum(intervals) / len(intervals)
                if mean_interval > 0:
                    cv = std_dev / mean_interval  # Coefficient of variation
                    # Low CV (consistent) = higher confidence
                    consistency_bonus = int(max(0, (1 - cv) * 20))
                    score = min(100, score + consistency_bonus)
            except Exception:
                pass

        return score

    def _predict_next_occurrence(
        self,
        dates: list[datetime],
        frequency: Frequency,
        intervals: list[int],
    ) -> datetime:
        """Predict the next expected occurrence.

        Uses average interval and last transaction date.
        """
        if not dates:
            return datetime.utcnow()

        last_date = max(dates)

        # Calculate average interval
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
        else:
            # Fall back to frequency window
            window, _ = self.FREQUENCY_WINDOWS[frequency]
            avg_interval = window

        next_expected = last_date + timedelta(days=avg_interval)
        return next_expected

    def _detect_anomalies(
        self,
        dates: list[datetime],
        frequency: Frequency,
    ) -> list[datetime]:
        """Detect dates where transactions were skipped or delayed.

        Returns list of expected dates where transactions did not occur.
        """
        if len(dates) < 2:
            return []

        sorted_dates = sorted(dates)
        window, tolerance = self.FREQUENCY_WINDOWS[frequency]
        skip_dates = []

        # Look for gaps larger than expected
        for i in range(1, len(sorted_dates)):
            delta = (sorted_dates[i] - sorted_dates[i - 1]).days
            expected_delta = window

            # If gap is significantly larger than expected, it likely skipped
            if delta > expected_delta + tolerance * 2:
                # Estimate intermediate missed dates
                num_missed = delta // expected_delta
                for j in range(1, num_missed):
                    estimated_date = sorted_dates[i - 1] + timedelta(days=expected_delta * j)
                    skip_dates.append(estimated_date)

        return skip_dates

    def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        """Save a user-approved recurring pattern to the database.

        Args:
            pattern: RecurringPattern to save

        Returns:
            Pattern with database ID populated
        """
        from backend.db.models.recurring_pattern import RecurringPattern as RecurringPatternModel

        db_pattern = RecurringPatternModel(
            merchant=pattern.merchant,
            category=pattern.category,
            average_amount=pattern.average_amount,
            amount_variance=pattern.amount_variance,
            frequency=pattern.frequency.value,
            next_expected=pattern.next_expected,
            confidence=pattern.confidence,
            occurrences=[d.isoformat() for d in pattern.occurrences],
            should_skip_dates=[d.isoformat() for d in pattern.should_skip_dates],
            is_active=True,
        )
        self.db.add(db_pattern)
        self.db.commit()
        self.db.refresh(db_pattern)

        pattern.id = db_pattern.id
        return pattern

    def get_recurring_patterns(self) -> list[RecurringPattern]:
        """Get all stored recurring patterns.

        Returns:
            List of user-approved RecurringPattern objects
        """
        from backend.db.models.recurring_pattern import RecurringPattern as RecurringPatternModel

        patterns = self.db.query(RecurringPatternModel).filter(
            RecurringPatternModel.is_active is True
        ).all()

        return [
            RecurringPattern(
                id=p.id,
                merchant=p.merchant,
                category=p.category,
                average_amount=Decimal(str(p.average_amount)),
                amount_variance=Decimal(str(p.amount_variance)),
                frequency=Frequency(p.frequency),
                next_expected=p.next_expected,
                confidence=p.confidence,
                occurrences=[datetime.fromisoformat(d) for d in (p.occurrences or [])],
                should_skip_dates=[datetime.fromisoformat(d) for d in (p.should_skip_dates or [])],
            )
            for p in patterns
        ]

    def delete_recurring_pattern(self, pattern_id: int) -> bool:
        """Delete a stored recurring pattern.

        Args:
            pattern_id: Database ID of pattern to delete

        Returns:
            True if successful
        """
        from backend.db.models.recurring_pattern import RecurringPattern as RecurringPatternModel

        pattern = self.db.query(RecurringPatternModel).filter(
            RecurringPatternModel.id == pattern_id
        ).first()

        if not pattern:
            return False

        self.db.delete(pattern)
        self.db.commit()
        return True

    def predict_next_occurrence(self, pattern_id: int) -> Optional[datetime]:
        """Predict next occurrence of a stored pattern.

        Args:
            pattern_id: Database ID of pattern

        Returns:
            Predicted datetime of next occurrence
        """
        from backend.db.models.recurring_pattern import RecurringPattern as RecurringPatternModel

        pattern = self.db.query(RecurringPatternModel).filter(
            RecurringPatternModel.id == pattern_id
        ).first()

        return pattern.next_expected if pattern else None
