"""Contextual insights service for alerts, anomalies, and predictions.

Provides:
- Budget warnings (over/under/on-track)
- Month-over-month comparisons
- Transaction anomaly detection
- Recurring transaction predictions

Refactored with strategy pattern to eliminate duplicated analysis logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session


@dataclass
class BudgetInsight:
    """Budget warning/insight."""

    category_name: str
    type: str  # "on_track" | "warning" | "critical"
    actual_spent: Decimal
    budget_limit: Decimal
    percent_used: float
    message: str


@dataclass
class MoMComparison:
    """Month-over-month comparison insight."""

    category_name: str
    current_month_amount: Decimal
    previous_month_amount: Decimal
    change_percent: float
    type: str  # "increase" | "decrease" | "stable"
    message: str


@dataclass
class TransactionAnomaly:
    """Anomalous transaction detection."""

    transaction_id: str
    merchant: str
    amount: Decimal
    category: str
    deviation_percent: float
    type: str  # "outlier" | "unusual_time" | "duplicate_pattern"
    message: str


@dataclass
class RecurringPrediction:
    """Predicted recurring transaction."""

    merchant: str
    category: str
    expected_amount: Decimal
    expected_date: date
    confidence: float
    message: str


# Strategy pattern base class
class InsightStrategy(ABC):
    """Base class for insight generation strategies."""

    @abstractmethod
    def run(self, db: Session, transaction_model, **kwargs):
        """Execute the insight analysis strategy."""
        pass


class BudgetAnalyzer(InsightStrategy):
    """Strategy for budget warning analysis."""

    def run(self, db: Session, transaction_model, **kwargs) -> list[BudgetInsight]:
        """Analyze budget warnings for current month."""
        category_id: Optional[str] = kwargs.get("category_id")
        insights = []
        today = date.today()
        month_start = date(today.year, today.month, 1)

        # Get transactions for current month by category
        txns = db.query(transaction_model).filter(
            transaction_model.date >= month_start,
            transaction_model.date <= today,
        ).all()

        category_totals: dict[str, Decimal] = {}
        for txn in txns:
            cat = txn.category or "Uncategorized"
            if cat not in category_totals:
                category_totals[cat] = Decimal("0")
            category_totals[cat] += abs(txn.amount)

        # For now, return generic insights based on spending patterns
        # In full implementation, would query Budget model
        for cat, total in category_totals.items():
            if total > Decimal("5000"):  # High spending threshold
                insights.append(
                    BudgetInsight(
                        category_name=cat,
                        type="warning",
                        actual_spent=total,
                        budget_limit=Decimal("5000"),
                        percent_used=float((total / Decimal("5000")) * 100),
                        message=f"High spending in {cat}: C${total:,.2f}",
                    )
                )

        return insights


class MoMAnalyzer(InsightStrategy):
    """Strategy for month-over-month analysis."""

    def run(self, db: Session, transaction_model, **kwargs) -> list[MoMComparison]:
        """Analyze month-over-month spending comparisons."""
        limit: int = kwargs.get("limit", 5)
        comparisons = []
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = date(previous_month_end.year, previous_month_end.month, 1)

        # Current month by category
        current_txns = db.query(transaction_model).filter(
            transaction_model.date >= current_month_start,
            transaction_model.date <= today,
        ).all()

        # Previous month by category
        previous_txns = db.query(transaction_model).filter(
            transaction_model.date >= previous_month_start,
            transaction_model.date <= previous_month_end,
        ).all()

        current_totals: dict[str, Decimal] = {}
        for txn in current_txns:
            cat = txn.category or "Uncategorized"
            if cat not in current_totals:
                current_totals[cat] = Decimal("0")
            current_totals[cat] += abs(txn.amount)

        previous_totals: dict[str, Decimal] = {}
        for txn in previous_txns:
            cat = txn.category or "Uncategorized"
            if cat not in previous_totals:
                previous_totals[cat] = Decimal("0")
            previous_totals[cat] += abs(txn.amount)

        # Calculate comparisons
        all_categories = set(current_totals.keys()) | set(previous_totals.keys())
        for cat in sorted(all_categories)[:limit]:
            current = current_totals.get(cat, Decimal("0"))
            previous = previous_totals.get(cat, Decimal("0"))

            if previous > 0:
                change_pct = float(((current - previous) / previous) * 100)
            else:
                change_pct = float(100 if current > 0 else 0)

            comparison_type = "increase" if change_pct > 5 else ("decrease" if change_pct < -5 else "stable")

            comparisons.append(
                MoMComparison(
                    category_name=cat,
                    current_month_amount=current,
                    previous_month_amount=previous,
                    change_percent=change_pct,
                    type=comparison_type,
                    message=f"{cat}: {change_pct:+.1f}% vs last month",
                )
            )

        return comparisons


class AnomalyDetector(InsightStrategy):
    """Strategy for transaction anomaly detection."""

    def run(self, db: Session, transaction_model, **kwargs) -> list[TransactionAnomaly]:
        """Detect unusual transactions."""
        limit: int = kwargs.get("limit", 5)
        anomalies = []
        today = date.today()
        month_start = date(today.year, today.month, 1)

        txns = db.query(transaction_model).filter(
            transaction_model.date >= month_start,
            transaction_model.date <= today,
        ).all()

        if len(txns) < 3:
            return anomalies

        # Calculate per-category stats
        category_amounts: dict[str, list[Decimal]] = {}
        for txn in txns:
            cat = txn.category or "Uncategorized"
            if cat not in category_amounts:
                category_amounts[cat] = []
            category_amounts[cat].append(abs(txn.amount))

        # Find outliers
        for txn in txns[-limit:]:  # Check recent transactions
            cat = txn.category or "Uncategorized"
            amounts = category_amounts.get(cat, [])

            if len(amounts) >= 3:
                avg = sum(amounts) / len(amounts)
                if avg > 0:
                    deviation = abs(abs(txn.amount) - avg) / avg * 100
                    if deviation > 100:  # More than 100% deviation
                        anomalies.append(
                            TransactionAnomaly(
                                transaction_id=str(txn.id),
                                merchant=txn.merchant,
                                amount=txn.amount,
                                category=cat,
                                deviation_percent=deviation,
                                type="outlier",
                                message=f"Unusual amount for {cat}: C${abs(txn.amount):,.2f}",
                            )
                        )

        return anomalies


class RecurringPredictor(InsightStrategy):
    """Strategy for recurring transaction prediction."""

    def run(self, db: Session, transaction_model, **kwargs) -> list[RecurringPrediction]:
        """Predict upcoming recurring transactions."""
        limit: int = kwargs.get("limit", 5)
        predictions = []
        today = date.today()
        three_months_ago = today - timedelta(days=90)

        txns = db.query(transaction_model).filter(
            transaction_model.date >= three_months_ago,
            transaction_model.date <= today,
        ).all()

        # Group by merchant to find patterns (store date, amount, category)
        merchant_txns: dict[str, list[tuple[date, Decimal, str]]] = {}
        for txn in txns:
            merchant = txn.merchant or "Unknown"
            if merchant not in merchant_txns:
                merchant_txns[merchant] = []
            # Convert datetime to date for date-only comparisons
            txn_date = txn.date.date() if hasattr(txn.date, 'date') else txn.date
            merchant_txns[merchant].append((txn_date, txn.amount, txn.category or "Unknown"))

        # Detect patterns (similar amounts, ~30 day intervals)
        for merchant, transactions in merchant_txns.items():
            if len(transactions) >= 2:
                # Sort by date
                sorted_txns = sorted(transactions, key=lambda x: x[0])

                # Check if amounts are similar (within 20%)
                amounts = [abs(amt) for _, amt, _ in sorted_txns]
                avg_amt = sum(amounts) / len(amounts)
                similar_amounts = all(
                    abs(amt - avg_amt) / avg_amt < 0.2 for amt in amounts
                )

                if similar_amounts and len(sorted_txns) >= 2:
                    # Estimate next date based on interval
                    dates = [d for d, _, _ in sorted_txns]
                    intervals = [
                        (dates[i + 1] - dates[i]).days
                        for i in range(len(dates) - 1)
                    ]
                    avg_interval = sum(intervals) / len(intervals)

                    if 20 < avg_interval < 40:  # Monthly-ish
                        confidence = 0.7 if len(intervals) >= 3 else 0.5
                        next_date = sorted_txns[-1][0] + timedelta(days=int(avg_interval))

                        if next_date > today and len(predictions) < limit:
                            predictions.append(
                                RecurringPrediction(
                                    merchant=merchant,
                                    category=sorted_txns[-1][2],
                                    expected_amount=avg_amt,
                                    expected_date=next_date,
                                    confidence=confidence,
                                    message=f"Expected {merchant} on {next_date.strftime('%b %d')}: C${avg_amt:,.2f}",
                                )
                            )

        return sorted(predictions, key=lambda x: x.expected_date)[:limit]


class ContextualInsightsService:
    """Service for generating contextual financial insights."""

    # Strategy registry
    STRATEGIES = {
        "budget": BudgetAnalyzer(),
        "mom": MoMAnalyzer(),
        "anomalies": AnomalyDetector(),
        "recurring": RecurringPredictor(),
    }

    def __init__(self, db: Session, transaction_model=None):
        self.db = db
        if transaction_model is None:
            # Import Transaction model from db models
            from backend.db.models import Transaction as DefaultTransaction
            self.transaction_model = DefaultTransaction
        else:
            self.transaction_model = transaction_model

    def analyze(self, insight_type: str, **kwargs):
        """Execute analysis using the specified strategy."""
        if insight_type not in self.STRATEGIES:
            raise ValueError(f"Unknown insight type: {insight_type}")

        strategy = self.STRATEGIES[insight_type]
        return strategy.run(self.db, self.transaction_model, **kwargs)

    # Backward-compatible methods (delegate to analyze())
    def get_budget_warnings(self, category_id: Optional[str] = None) -> list[BudgetInsight]:
        """Get budget warning insights for current month."""
        return self.analyze("budget", category_id=category_id)

    def get_mom_comparisons(self, limit: int = 5) -> list[MoMComparison]:
        """Get month-over-month spending comparisons."""
        return self.analyze("mom", limit=limit)

    def detect_anomalies(self, limit: int = 5) -> list[TransactionAnomaly]:
        """Detect unusual transactions."""
        return self.analyze("anomalies", limit=limit)

    def predict_recurring(self, limit: int = 5) -> list[RecurringPrediction]:
        """Predict upcoming recurring transactions."""
        return self.analyze("recurring", limit=limit)
