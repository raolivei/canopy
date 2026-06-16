"""Cashflow aggregation service for monthly income/expense metrics.

Canopy - Personal Finance Platform
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction as TransactionModel


class CashflowService:
    """Service for calculating monthly cashflow metrics."""

    def __init__(self, db: Session):
        """Initialize cashflow service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_monthly_summary(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Calculate income, expenses, and net for each month in date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            List of monthly summaries with income, expenses, and net amounts
        """
        query = select(TransactionModel).where(
            TransactionModel.date >= start_date,
            TransactionModel.date <= end_date,
        )

        transactions = self.db.execute(query).scalars().all()

        # Group transactions by month
        monthly_data: dict[str, dict[str, float]] = {}

        for tx in transactions:
            month_key = tx.date.strftime("%Y-%m")

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "income": 0.0,
                    "expenses": 0.0,
                }

            if tx.type == "income":
                monthly_data[month_key]["income"] += float(tx.amount)
            elif tx.type == "expense":
                monthly_data[month_key]["expenses"] += float(abs(tx.amount))

        # Convert to sorted list with net calculations
        result = []
        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            income = data["income"]
            expenses = data["expenses"]
            net = income - expenses

            result.append({
                "month": month_key,
                "income": income,
                "expenses": expenses,
                "net": net,
                "currency": "CAD",
            })

        return result

    def get_cashflow_trend(self, months: int = 12) -> dict[str, Any]:
        """Get cashflow trend over N months.

        Args:
            months: Number of months to analyze (default: 12)

        Returns:
            Dictionary with monthly data and trend analysis
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        monthly_summary = self.get_monthly_summary(start_date, end_date)

        # Calculate averages and trends
        if not monthly_summary:
            return {
                "months": months,
                "monthly_data": [],
                "average_income": 0.0,
                "average_expenses": 0.0,
                "average_net": 0.0,
                "trend": "no_data",
                "currency": "CAD",
            }

        total_income = sum(m["income"] for m in monthly_summary)
        total_expenses = sum(m["expenses"] for m in monthly_summary)
        total_net = sum(m["net"] for m in monthly_summary)

        avg_income = total_income / len(monthly_summary)
        avg_expenses = total_expenses / len(monthly_summary)
        avg_net = total_net / len(monthly_summary)

        # Determine trend (compare last 3 months vs previous 3 months)
        trend = "stable"
        if len(monthly_summary) >= 6:
            recent_avg_net = sum(m["net"] for m in monthly_summary[-3:]) / 3
            previous_avg_net = sum(m["net"] for m in monthly_summary[-6:-3]) / 3

            if recent_avg_net > previous_avg_net * 1.1:
                trend = "improving"
            elif recent_avg_net < previous_avg_net * 0.9:
                trend = "declining"

        return {
            "months": months,
            "monthly_data": monthly_summary,
            "average_income": avg_income,
            "average_expenses": avg_expenses,
            "average_net": avg_net,
            "trend": trend,
            "currency": "CAD",
        }

    def get_category_breakdown(self, month: Optional[str] = None) -> dict[str, Any]:
        """Get expense breakdown by category for a specific month.

        Args:
            month: Month in YYYY-MM format (defaults to current month)

        Returns:
            Dictionary with category breakdown and totals
        """
        if month is None:
            today = date.today()
            month = f"{today.year}-{today.month:02d}"

        # Parse month string
        year, month_num = map(int, month.split("-"))
        month_start = date(year, month_num, 1)

        # Get last day of month
        if month_num == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month_num + 1, 1) - timedelta(days=1)

        # Get expense transactions for month
        query = select(TransactionModel).where(
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end,
            TransactionModel.type == "expense",
        )

        transactions = self.db.execute(query).scalars().all()

        # Group by category
        category_totals: dict[str, float] = {}
        for tx in transactions:
            category = tx.category or "Uncategorized"
            category_totals[category] = category_totals.get(category, 0) + float(
                abs(tx.amount)
            )

        total_expenses = sum(category_totals.values())

        # Convert to sorted list with percentages
        categories = [
            {
                "category": cat,
                "amount": amount,
                "percentage": (amount / total_expenses * 100) if total_expenses > 0 else 0,
            }
            for cat, amount in category_totals.items()
        ]

        categories.sort(key=lambda x: x["amount"], reverse=True)

        return {
            "month": month,
            "total_expenses": total_expenses,
            "categories": categories,
            "currency": "CAD",
        }

    def calculate_burn_rate(self, months: int = 3) -> dict[str, Any]:
        """Calculate average monthly spending (burn rate).

        Args:
            months: Number of months to analyze (default: 3)

        Returns:
            Dictionary with burn rate metrics
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        query = select(TransactionModel).where(
            TransactionModel.date >= start_date,
            TransactionModel.date <= end_date,
            TransactionModel.type == "expense",
        )

        transactions = self.db.execute(query).scalars().all()

        # Calculate monthly expenses
        monthly_expenses: dict[str, float] = {}

        for tx in transactions:
            month_key = tx.date.strftime("%Y-%m")
            monthly_expenses[month_key] = monthly_expenses.get(month_key, 0) + float(
                abs(tx.amount)
            )

        if not monthly_expenses:
            return {
                "months_analyzed": months,
                "average_monthly_burn": 0.0,
                "monthly_breakdown": [],
                "min_month": None,
                "max_month": None,
                "volatility": "no_data",
                "currency": "CAD",
            }

        # Calculate statistics
        monthly_values = list(monthly_expenses.values())
        avg_burn = sum(monthly_values) / len(monthly_values)
        min_burn = min(monthly_values)
        max_burn = max(monthly_values)

        # Find months with min/max
        min_month = next(
            month for month, val in monthly_expenses.items() if val == min_burn
        )
        max_month = next(
            month for month, val in monthly_expenses.items() if val == max_burn
        )

        # Calculate volatility
        if avg_burn > 0:
            variance = sum((val - avg_burn) ** 2 for val in monthly_values) / len(
                monthly_values
            )
            std_dev = variance**0.5
            coefficient_of_variation = (std_dev / avg_burn) * 100

            if coefficient_of_variation < 10:
                volatility = "low"
            elif coefficient_of_variation < 20:
                volatility = "moderate"
            else:
                volatility = "high"
        else:
            volatility = "no_data"

        # Build monthly breakdown
        monthly_breakdown = [
            {"month": month, "amount": amount}
            for month, amount in sorted(monthly_expenses.items())
        ]

        return {
            "months_analyzed": len(monthly_expenses),
            "average_monthly_burn": avg_burn,
            "monthly_breakdown": monthly_breakdown,
            "min_month": {"month": min_month, "amount": min_burn},
            "max_month": {"month": max_month, "amount": max_burn},
            "volatility": volatility,
            "currency": "CAD",
        }
