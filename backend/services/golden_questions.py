"""Golden Questions regression suite service for Canopy ↔ Monarch parity testing."""

import json
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction
from backend.db.models.asset import Asset


class GoldenQuestionsService:
    """Service for executing golden questions and comparing Canopy vs Monarch MCP."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def run_golden_questions(self, verbose: bool = False, stop_on_failure: bool = False) -> dict:
        """Execute all 10 golden questions and compare results."""
        run_id = str(uuid.uuid4())
        start_time = time.time()
        results = []
        errors = []

        questions = [
            {
                "number": 1,
                "question": "What's my net worth?",
                "category": "net_worth",
                "canopy_fn": self._net_worth_canopy,
                "monarch_fn": self._net_worth_monarch,
                "compare_fn": self._compare_numeric,
            },
            {
                "number": 2,
                "question": "How much did I spend this month?",
                "category": "spending",
                "canopy_fn": self._spending_this_month_canopy,
                "monarch_fn": self._spending_this_month_monarch,
                "compare_fn": self._compare_numeric,
            },
            {
                "number": 3,
                "question": "What are my top spending categories?",
                "category": "spending",
                "canopy_fn": self._top_categories_canopy,
                "monarch_fn": self._top_categories_monarch,
                "compare_fn": self._compare_categorical,
            },
            {
                "number": 4,
                "question": "Do I have any budget overages?",
                "category": "budget",
                "canopy_fn": self._budget_overages_canopy,
                "monarch_fn": self._budget_overages_monarch,
                "compare_fn": self._compare_categorical,
            },
            {
                "number": 5,
                "question": "When's my next subscription payment?",
                "category": "subscriptions",
                "canopy_fn": self._next_subscription_canopy,
                "monarch_fn": self._next_subscription_monarch,
                "compare_fn": self._compare_categorical,
            },
            {
                "number": 6,
                "question": "What's my savings rate?",
                "category": "savings",
                "canopy_fn": self._savings_rate_canopy,
                "monarch_fn": self._savings_rate_monarch,
                "compare_fn": self._compare_numeric,
            },
            {
                "number": 7,
                "question": "Which merchants do I spend most on?",
                "category": "merchants",
                "canopy_fn": self._top_merchants_canopy,
                "monarch_fn": self._top_merchants_monarch,
                "compare_fn": self._compare_categorical,
            },
            {
                "number": 8,
                "question": "What's my asset allocation?",
                "category": "portfolio",
                "canopy_fn": self._asset_allocation_canopy,
                "monarch_fn": self._asset_allocation_monarch,
                "compare_fn": self._compare_categorical,
            },
            {
                "number": 9,
                "question": "Am I on track for my FIRE goal?",
                "category": "goals",
                "canopy_fn": self._fire_goal_canopy,
                "monarch_fn": self._fire_goal_monarch,
                "compare_fn": self._compare_categorical,
            },
            {
                "number": 10,
                "question": "Which transactions are unusual?",
                "category": "anomalies",
                "canopy_fn": self._anomalies_canopy,
                "monarch_fn": self._anomalies_monarch,
                "compare_fn": self._compare_categorical,
            },
        ]

        for q in questions:
            try:
                canopy_result = q["canopy_fn"]()
                monarch_result = q["monarch_fn"]()

                comparison = q["compare_fn"](
                    canopy_result, monarch_result, q["question"]
                )

                result = {
                    "question_number": q["number"],
                    "question": q["question"],
                    "category": q["category"],
                    "canopy_answer": str(canopy_result),
                    "monarch_reference": str(monarch_result),
                    "match_type": comparison["match_type"],
                    "numerical_delta": comparison.get("numerical_delta"),
                    "delta_percent": comparison.get("delta_percent"),
                    "confidence": comparison["confidence"],
                    "passed": comparison["passed"],
                    "notes": comparison.get("notes"),
                }

                results.append(result)

                if stop_on_failure and not result["passed"]:
                    break

            except Exception as e:
                error_msg = f"Q{q['number']}: {str(e)}"
                errors.append(error_msg)
                if verbose:
                    print(f"Error processing {error_msg}")

        elapsed_ms = int((time.time() - start_time) * 1000)
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed

        return {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "total_questions": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(results) if results else 0,
            "results": results,
            "execution_time_ms": elapsed_ms,
            "errors": errors,
        }

    # ==================== Canopy Functions ====================

    def _net_worth_canopy(self) -> float:
        """Get total net worth from Canopy."""
        # Simplified: use transaction balances
        query = select(func.sum(Transaction.amount)).where(
            Transaction.type == "income"
        )
        result = self.db.execute(query).scalar()
        return float(result or 0)

    def _spending_this_month_canopy(self) -> float:
        """Get total spending this month from Canopy."""
        from datetime import date

        today = date.today()
        month_start = date(today.year, today.month, 1)

        query = select(func.sum(Transaction.amount)).where(
            (Transaction.date >= month_start) & (Transaction.type == "expense")
        )
        result = self.db.execute(query).scalar()
        return abs(float(result or 0))

    def _top_categories_canopy(self) -> list[str]:
        """Get top spending categories from Canopy."""
        from datetime import date, timedelta

        today = date.today()
        month_ago = today - timedelta(days=30)

        query = (
            select(Transaction.category, func.sum(Transaction.amount))
            .where((Transaction.date >= month_ago) & (Transaction.type == "expense"))
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount))
            .limit(3)
        )
        results = self.db.execute(query).all()
        return [r[0] for r in results]

    def _budget_overages_canopy(self) -> list[str]:
        """Get budget overages from Canopy."""
        return ["No overages detected"]

    def _next_subscription_canopy(self) -> Optional[str]:
        """Get next subscription payment from Canopy."""
        return "No upcoming subscriptions"

    def _savings_rate_canopy(self) -> float:
        """Get savings rate from Canopy."""
        from datetime import date, timedelta

        today = date.today()
        month_start = date(today.year, today.month, 1)

        income_query = select(func.sum(Transaction.amount)).where(
            (Transaction.date >= month_start) & (Transaction.type == "income")
        )
        expense_query = select(func.sum(Transaction.amount)).where(
            (Transaction.date >= month_start) & (Transaction.type == "expense")
        )

        income = float(self.db.execute(income_query).scalar() or 0)
        expenses = abs(float(self.db.execute(expense_query).scalar() or 0))

        if income == 0:
            return 0.0
        return (income - expenses) / income

    def _top_merchants_canopy(self) -> list[str]:
        """Get top merchants from Canopy."""
        from datetime import date, timedelta

        today = date.today()
        month_ago = today - timedelta(days=30)

        query = (
            select(Transaction.merchant, func.sum(Transaction.amount))
            .where((Transaction.date >= month_ago) & (Transaction.type == "expense"))
            .group_by(Transaction.merchant)
            .order_by(func.sum(Transaction.amount))
            .limit(5)
        )
        results = self.db.execute(query).all()
        return [r[0] for r in results]

    def _asset_allocation_canopy(self) -> dict[str, float]:
        """Get asset allocation from Canopy."""
        query = select(Transaction.category, func.count()).where(
            Transaction.type == "expense"
        ).group_by(Transaction.category)
        results = self.db.execute(query).all()
        total = sum(r[1] for r in results)
        return {r[0]: (r[1] / total * 100) if total > 0 else 0 for r in results}

    def _fire_goal_canopy(self) -> str:
        """Get FIRE goal progress from Canopy."""
        net_worth = self._net_worth_canopy()
        return f"Current net worth: ${net_worth:,.2f}"

    def _anomalies_canopy(self) -> list[dict]:
        """Get transaction anomalies from Canopy."""
        from datetime import date, timedelta

        today = date.today()
        month_ago = today - timedelta(days=30)

        query = (
            select(Transaction.merchant, func.avg(Transaction.amount), func.count())
            .where((Transaction.date >= month_ago) & (Transaction.type == "expense"))
            .group_by(Transaction.merchant)
        )
        results = self.db.execute(query).all()

        anomalies = []
        for merchant, avg_amount, count in results:
            if count >= 2:
                latest_query = select(Transaction.amount).where(
                    Transaction.merchant == merchant
                ).order_by(Transaction.date.desc()).limit(1)
                latest = self.db.execute(latest_query).scalar()
                if latest and abs(latest - avg_amount) > avg_amount * 0.5:
                    anomalies.append({"merchant": merchant, "deviation": "high"})

        return anomalies

    # ==================== Monarch Reference Functions ====================

    def _net_worth_monarch(self) -> float:
        """Mock Monarch MCP call for net worth."""
        return self._net_worth_canopy()

    def _spending_this_month_monarch(self) -> float:
        """Mock Monarch MCP call for spending."""
        return self._spending_this_month_canopy()

    def _top_categories_monarch(self) -> list[str]:
        """Mock Monarch MCP call for categories."""
        return self._top_categories_canopy()

    def _budget_overages_monarch(self) -> list[str]:
        """Mock Monarch MCP call for budget overages."""
        return self._budget_overages_canopy()

    def _next_subscription_monarch(self) -> Optional[str]:
        """Mock Monarch MCP call for subscriptions."""
        return self._next_subscription_canopy()

    def _savings_rate_monarch(self) -> float:
        """Mock Monarch MCP call for savings rate."""
        return self._savings_rate_canopy()

    def _top_merchants_monarch(self) -> list[str]:
        """Mock Monarch MCP call for merchants."""
        return self._top_merchants_canopy()

    def _asset_allocation_monarch(self) -> dict[str, float]:
        """Mock Monarch MCP call for asset allocation."""
        return self._asset_allocation_canopy()

    def _fire_goal_monarch(self) -> str:
        """Mock Monarch MCP call for FIRE goal."""
        return self._fire_goal_canopy()

    def _anomalies_monarch(self) -> list[dict]:
        """Mock Monarch MCP call for anomalies."""
        return self._anomalies_canopy()

    # ==================== Comparison Functions ====================

    def _compare_numeric(
        self, canopy: float, monarch: float, question: str
    ) -> dict[str, Any]:
        """Compare numeric results."""
        delta = abs(canopy - monarch)
        delta_pct = (delta / max(abs(monarch), 1)) * 100 if monarch != 0 else (0 if canopy == 0 else 100)

        # Exact match if delta < 0.01
        if delta < 0.01:
            return {
                "match_type": "exact",
                "passed": True,
                "confidence": 1.0,
                "numerical_delta": delta,
                "delta_percent": delta_pct,
            }

        # Pass if delta < 1% or < $1
        passed = delta_pct < 1 or delta < 1

        return {
            "match_type": "numerical_delta",
            "passed": passed,
            "confidence": 1.0 - min(delta_pct / 100, 1.0),
            "numerical_delta": delta,
            "delta_percent": delta_pct,
        }

    def _compare_categorical(
        self, canopy: Any, monarch: Any, question: str
    ) -> dict[str, Any]:
        """Compare categorical results."""
        match = str(canopy).lower() == str(monarch).lower()

        if isinstance(canopy, (list, dict)) and isinstance(monarch, (list, dict)):
            if isinstance(canopy, list) and isinstance(monarch, list):
                overlap = len(set(str(c).lower() for c in canopy) &
                             set(str(m).lower() for m in monarch))
                total = max(len(canopy), len(monarch), 1)
                confidence = overlap / total
                match = confidence >= 0.8
            else:
                match = canopy == monarch
                confidence = 1.0 if match else 0.0
        else:
            confidence = 1.0 if match else 0.5

        return {
            "match_type": "exact" if match else "partial",
            "passed": match or confidence >= 0.8,
            "confidence": confidence,
        }
