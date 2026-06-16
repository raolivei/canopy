"""Recurring transaction detection service for identifying patterns and predictions.

Canopy - Personal Finance Platform
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction as TransactionModel
from backend.models.recurring import (
    RecurringPattern,
    RecurringPrediction,
)


class RecurringDetectionService:
    """Service for detecting recurring transaction patterns and predictions."""

    def __init__(self, db: Session):
        """Initialize recurring detection service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def detect_recurring_patterns(self, months: int = 3) -> list[RecurringPattern]:
        """Detect recurring transaction patterns over a time period.

        Analyzes transactions to find recurring patterns based on:
        - Same merchant
        - Similar amounts (±10% variance)
        - Regular intervals (7, 14, 30 days)
        - Minimum 3 occurrences

        Args:
            months: Number of months to analyze (default: 3)

        Returns:
            List of detected recurring patterns with confidence scores
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        # Get all expense transactions in the period
        query = (
            select(TransactionModel)
            .where(
                TransactionModel.date >= start_date,
                TransactionModel.date <= end_date,
                TransactionModel.type == "expense",
                TransactionModel.merchant.isnot(None),
            )
            .order_by(TransactionModel.date)
        )

        transactions = self.db.execute(query).scalars().all()

        # Group transactions by merchant
        merchant_transactions: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for tx in transactions:
            merchant_transactions[tx.merchant].append(
                {
                    "id": tx.id,
                    "date": tx.date.date() if hasattr(tx.date, "date") else tx.date,
                    "amount": float(abs(tx.amount)),
                    "category": tx.category or "Uncategorized",
                }
            )

        # Detect patterns for each merchant
        patterns: list[RecurringPattern] = []

        for merchant, txns in merchant_transactions.items():
            # Need at least 3 transactions
            if len(txns) < 3:
                continue

            # Sort by date
            txns.sort(key=lambda x: x["date"])

            # Calculate intervals between transactions
            intervals = []
            for i in range(1, len(txns)):
                days_diff = (txns[i]["date"] - txns[i - 1]["date"]).days
                intervals.append(days_diff)

            if not intervals:
                continue

            # Check for regular intervals (7, 14, 30 days with ±3 day tolerance)
            avg_interval = sum(intervals) / len(intervals)

            # Determine if this is a weekly, biweekly, or monthly pattern
            frequency_days = None
            if 4 <= avg_interval <= 10:
                frequency_days = 7  # Weekly
            elif 11 <= avg_interval <= 17:
                frequency_days = 14  # Biweekly
            elif 25 <= avg_interval <= 35:
                frequency_days = 30  # Monthly
            else:
                continue  # Not a recognized pattern

            # Calculate amount variance
            amounts = [tx["amount"] for tx in txns]
            avg_amount = sum(amounts) / len(amounts)

            # Check if amounts are within ±10% variance
            within_variance = all(
                abs(amount - avg_amount) / avg_amount <= 0.10 for amount in amounts
            )

            if not within_variance:
                continue

            # Calculate confidence score based on:
            # - Number of occurrences (more = higher confidence)
            # - Interval consistency (less variance = higher confidence)
            # - Amount consistency (already checked ±10%)

            occurrence_score = min(len(txns) / 10, 1.0)  # Max at 10 occurrences

            # Interval consistency: how close intervals are to frequency_days
            interval_variance = sum(
                abs(interval - frequency_days) for interval in intervals
            ) / len(intervals)
            interval_score = max(0, 1.0 - (interval_variance / frequency_days))

            confidence = (occurrence_score * 0.5) + (interval_score * 0.5)
            confidence = round(confidence, 2)

            # Predict next occurrence
            last_date = txns[-1]["date"]
            predicted_next = last_date + timedelta(days=frequency_days)

            patterns.append(
                RecurringPattern(
                    merchant=merchant,
                    category=txns[0]["category"],  # Use first transaction's category
                    avg_amount=round(avg_amount, 2),
                    frequency_days=frequency_days,
                    confidence=confidence,
                    last_occurrence=last_date,
                    predicted_next=predicted_next,
                    occurrences=len(txns),
                )
            )

        # Sort by confidence (highest first)
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        return patterns

    def get_recurring_predictions(
        self, next_days: int = 30
    ) -> list[RecurringPrediction]:
        """Get predictions for recurring transactions in the next N days.

        Args:
            next_days: Number of days ahead to predict (default: 30)

        Returns:
            List of predicted recurring transactions within the time window
        """
        # Detect patterns (using last 3 months)
        patterns = self.detect_recurring_patterns(months=3)

        predictions: list[RecurringPrediction] = []
        today = date.today()
        prediction_end = today + timedelta(days=next_days)

        for pattern in patterns:
            # Check if predicted next occurrence is within window
            if today <= pattern.predicted_next <= prediction_end:
                days_until = (pattern.predicted_next - today).days

                # Calculate amount range (±10%)
                amount_min = round(pattern.avg_amount * 0.9, 2)
                amount_max = round(pattern.avg_amount * 1.1, 2)

                predictions.append(
                    RecurringPrediction(
                        pattern=pattern,
                        days_until_next=days_until,
                        amount_range=(amount_min, amount_max),
                    )
                )

        # Sort by days_until_next (soonest first)
        predictions.sort(key=lambda p: p.days_until_next)

        return predictions

    def classify_transaction(self, txn_id: int) -> dict[str, Any]:
        """Check if a specific transaction matches a recurring pattern.

        Args:
            txn_id: Transaction ID to classify

        Returns:
            Dictionary with is_recurring, confidence, and pattern (if applicable)
        """
        # Get the transaction
        query = select(TransactionModel).where(TransactionModel.id == txn_id)
        transaction = self.db.execute(query).scalar_one_or_none()

        if not transaction:
            return {
                "is_recurring": False,
                "confidence": None,
                "pattern": None,
            }

        # Get all patterns
        patterns = self.detect_recurring_patterns(months=6)  # Look back 6 months

        # Check if transaction matches any pattern
        for pattern in patterns:
            # Match by merchant and amount range
            if transaction.merchant == pattern.merchant:
                amount = float(abs(transaction.amount))
                amount_min = pattern.avg_amount * 0.9
                amount_max = pattern.avg_amount * 1.1

                if amount_min <= amount <= amount_max:
                    return {
                        "is_recurring": True,
                        "confidence": pattern.confidence,
                        "pattern": pattern,
                    }

        return {
            "is_recurring": False,
            "confidence": None,
            "pattern": None,
        }
