"""Cashflow analysis service for monthly income, expenses, and savings metrics.

Canopy - Personal Finance Platform
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction, TransactionType


class CashflowService:
    """Calculates monthly cashflow metrics (income, expenses, savings, trends)."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy session for database access
        """
        self.db = db

    def _get_month_key(self, date_obj: datetime) -> str:
        """Format datetime to YYYY-MM string."""
        return date_obj.strftime("%Y-%m")

    def _get_transactions_for_month(
        self, year: int, month: int, transaction_types: list[str]
    ) -> list[Transaction]:
        """Get all transactions for a specific month and types.

        Args:
            year: Year (e.g., 2026)
            month: Month (1-12)
            transaction_types: List of TransactionType values to include

        Returns:
            List of transactions matching the criteria
        """
        stmt = select(Transaction).where(
            and_(
                func.extract("year", Transaction.date) == year,
                func.extract("month", Transaction.date) == month,
                Transaction.type.in_(transaction_types),
            )
        )
        return self.db.execute(stmt).scalars().all()

    def _sum_transactions(self, transactions: list[Transaction]) -> Decimal:
        """Sum amounts from a list of transactions.

        Args:
            transactions: List of transactions to sum

        Returns:
            Total amount as Decimal (sum of transaction.amount fields)
        """
        total = Decimal("0.00")
        for txn in transactions:
            total += txn.amount
        return total

    def get_monthly_metrics(self, year: int, month: int) -> dict[str, Any]:
        """Get monthly cashflow metrics (income, expenses, savings, top categories).

        Args:
            year: Year (e.g., 2026)
            month: Month (1-12)

        Returns:
            Dictionary with:
            - month: "YYYY-MM"
            - income: Total income (Decimal)
            - expenses: Total expenses (Decimal)
            - savings: Income - Expenses (Decimal)
            - savings_rate: Percentage (0.0 if no income)
            - categories: List of top expense categories with amounts
        """
        # Get income transactions
        income_txns = self._get_transactions_for_month(
            year, month, [TransactionType.INCOME]
        )
        total_income = self._sum_transactions(income_txns)

        # Get expense transactions
        expense_txns = self._get_transactions_for_month(
            year, month, [TransactionType.EXPENSE]
        )
        total_expenses = self._sum_transactions(expense_txns)

        # Calculate savings
        savings = total_income - total_expenses
        savings_rate = (
            float((savings / total_income * 100))
            if total_income > Decimal("0")
            else Decimal("0")
        )

        # Get top expense categories
        categories_dict: dict[str, Decimal] = {}
        for txn in expense_txns:
            category = txn.category or "Uncategorized"
            categories_dict[category] = categories_dict.get(category, Decimal("0")) + txn.amount

        # Sort by amount descending and format
        top_categories = [
            {"category": cat, "amount": float(amount)}
            for cat, amount in sorted(
                categories_dict.items(), key=lambda x: x[1], reverse=True
            )[:10]  # Top 10 categories
        ]

        month_key = f"{year:04d}-{month:02d}"

        return {
            "month": month_key,
            "income": float(total_income),
            "expenses": float(total_expenses),
            "savings": float(savings),
            "savings_rate": float(savings_rate),
            "categories": top_categories,
        }

    def get_cashflow_trend(self, months: int = 12) -> list[dict[str, Any]]:
        """Get cashflow metrics for the last N months.

        Args:
            months: Number of months to include (default 12)

        Returns:
            List of monthly metrics, ordered from oldest to newest
        """
        # Get the date range for the last N months
        today = datetime.now()

        # Start from the beginning of the month N months ago
        year = today.year
        month = today.month

        trend = []

        for _ in range(months):
            metrics = self.get_monthly_metrics(year, month)
            trend.insert(0, metrics)  # Insert at beginning to maintain order

            # Move to previous month
            month -= 1
            if month < 1:
                month = 12
                year -= 1

        return trend

    def get_cashflow_summary(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get aggregate cashflow summary for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dictionary with:
            - total_income: Sum of all income transactions
            - total_expenses: Sum of all expense transactions
            - total_savings: Income - Expenses
            - average_monthly_savings: Average per-month savings
            - trend: "up", "down", or "stable"
        """
        # Get all transactions in the date range (income and expenses only)
        stmt = select(Transaction).where(
            and_(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            )
        )
        transactions = self.db.execute(stmt).scalars().all()

        # Separate income and expenses
        total_income = Decimal("0.00")
        total_expenses = Decimal("0.00")

        for txn in transactions:
            if txn.type == TransactionType.INCOME:
                total_income += txn.amount
            elif txn.type == TransactionType.EXPENSE:
                total_expenses += txn.amount

        total_savings = total_income - total_expenses

        # Calculate number of months for averaging
        num_months = max(1, self._get_month_count(start_date, end_date))
        average_monthly_savings = total_savings / Decimal(str(num_months))

        # Determine trend by comparing first and second halves
        trend = self._calculate_trend(start_date, end_date)

        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "total_savings": float(total_savings),
            "average_monthly_savings": float(average_monthly_savings),
            "trend": trend,
        }

    def _get_month_count(self, start_date: datetime, end_date: datetime) -> int:
        """Calculate the number of months between two dates.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of months (at least 1)
        """
        months = (end_date.year - start_date.year) * 12 + (
            end_date.month - start_date.month
        )
        return max(1, months + 1)  # +1 to include both start and end months

    def _calculate_trend(self, start_date: datetime, end_date: datetime) -> str:
        """Calculate trend by comparing savings rates between first and second halves.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            "up", "down", or "stable"
        """
        # Calculate mid-date
        total_days = (end_date - start_date).days
        mid_date = datetime.fromordinal(
            start_date.toordinal() + total_days // 2
        )

        # Get savings rates for each half
        first_half_income = self._sum_transactions(
            self.db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= mid_date,
                        Transaction.type == TransactionType.INCOME,
                    )
                )
            )
            .scalars()
            .all()
        )
        first_half_expenses = self._sum_transactions(
            self.db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= mid_date,
                        Transaction.type == TransactionType.EXPENSE,
                    )
                )
            )
            .scalars()
            .all()
        )

        second_half_income = self._sum_transactions(
            self.db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.date > mid_date,
                        Transaction.date <= end_date,
                        Transaction.type == TransactionType.INCOME,
                    )
                )
            )
            .scalars()
            .all()
        )
        second_half_expenses = self._sum_transactions(
            self.db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.date > mid_date,
                        Transaction.date <= end_date,
                        Transaction.type == TransactionType.EXPENSE,
                    )
                )
            )
            .scalars()
            .all()
        )

        # Calculate savings rates (with safe division)
        first_half_savings = first_half_income - first_half_expenses
        second_half_savings = second_half_income - second_half_expenses

        if first_half_income == Decimal("0") or second_half_income == Decimal("0"):
            return "stable"

        first_rate = first_half_savings / first_half_income
        second_rate = second_half_savings / second_half_income

        # Determine trend with a threshold
        difference = second_rate - first_rate
        threshold = Decimal("0.05")  # 5% threshold for "stable"

        if difference > threshold:
            return "up"
        elif difference < -threshold:
            return "down"
        else:
            return "stable"
