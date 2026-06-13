"""Budget tracking service for comparing actual spending against limits.

Canopy - Personal Finance Platform
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.db.models.budget import Budget, BudgetCategory, BudgetTracking, PeriodType
from backend.db.models.transaction import Transaction, TransactionType


class BudgetService:
    """Calculates budget tracking and variance metrics."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy session for database access
        """
        self.db = db

    # ==================== BUDGET CRUD ====================

    def create_budget(
        self, name: str, currency: str = "CAD", description: Optional[str] = None
    ) -> Budget:
        """Create a new budget.

        Args:
            name: Budget name (must not be empty)
            currency: Currency code (default: CAD)
            description: Optional description

        Returns:
            Created Budget instance

        Raises:
            ValueError: If name is empty
        """
        if not name or not name.strip():
            raise ValueError("Budget name cannot be empty")

        budget = Budget(
            name=name.strip(),
            currency=currency,
            description=description.strip() if description else None,
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def get_budget(self, budget_id: int) -> Optional[Budget]:
        """Get a budget by ID with all its categories.

        Args:
            budget_id: Budget ID

        Returns:
            Budget instance or None if not found
        """
        return self.db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()

    def list_budgets(self, active_only: bool = False) -> list[Budget]:
        """List all budgets.

        Args:
            active_only: If True, only return active budgets

        Returns:
            List of Budget instances
        """
        query = select(Budget)
        if active_only:
            query = query.where(Budget.is_active)
        return self.db.execute(query).scalars().all()

    def update_budget(
        self,
        budget_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Budget]:
        """Update a budget.

        Args:
            budget_id: Budget ID
            name: New name (if provided)
            description: New description (if provided)
            is_active: New active status (if provided)

        Returns:
            Updated Budget instance or None if not found

        Raises:
            ValueError: If name is provided but empty
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return None

        if name is not None:
            if not name or not name.strip():
                raise ValueError("Budget name cannot be empty")
            budget.name = name.strip()

        if description is not None:
            budget.description = description.strip() if description else None

        if is_active is not None:
            budget.is_active = is_active

        self.db.commit()
        self.db.refresh(budget)
        return budget

    def delete_budget(self, budget_id: int) -> bool:
        """Delete a budget and all associated data.

        Args:
            budget_id: Budget ID

        Returns:
            True if deleted, False if not found
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return False

        self.db.delete(budget)
        self.db.commit()
        return True

    # ==================== BUDGET CATEGORY CRUD ====================

    def add_category_to_budget(
        self,
        budget_id: int,
        category_name: str,
        limit_amount: Decimal,
        period_type: str = "monthly",
        rollover_excess: bool = False,
    ) -> Optional[BudgetCategory]:
        """Add a spending category to a budget.

        Args:
            budget_id: Budget ID
            category_name: Category name (e.g., "Groceries")
            limit_amount: Monthly/quarterly/annual limit
            period_type: "monthly", "quarterly", or "annual"
            rollover_excess: If True, unused balance carries to next period

        Returns:
            Created BudgetCategory or None if budget not found

        Raises:
            ValueError: If inputs invalid
        """
        if not category_name or not category_name.strip():
            raise ValueError("Category name cannot be empty")

        if limit_amount <= 0:
            raise ValueError("Limit amount must be greater than 0")

        if period_type not in [pt.value for pt in PeriodType]:
            raise ValueError(f"Invalid period_type: {period_type}")

        budget = self.get_budget(budget_id)
        if not budget:
            return None

        budget_category = BudgetCategory(
            budget_id=budget_id,
            category_name=category_name.strip(),
            limit_amount=limit_amount,
            period_type=period_type,
            rollover_excess=rollover_excess,
        )
        self.db.add(budget_category)
        self.db.commit()
        self.db.refresh(budget_category)
        return budget_category

    def update_budget_category(
        self,
        category_id: int,
        limit_amount: Optional[Decimal] = None,
        rollover_excess: Optional[bool] = None,
    ) -> Optional[BudgetCategory]:
        """Update a budget category.

        Args:
            category_id: BudgetCategory ID
            limit_amount: New limit amount (if provided)
            rollover_excess: New rollover setting (if provided)

        Returns:
            Updated BudgetCategory or None if not found

        Raises:
            ValueError: If limit_amount <= 0
        """
        category = self.db.execute(
            select(BudgetCategory).where(BudgetCategory.id == category_id)
        ).scalar_one_or_none()

        if not category:
            return None

        if limit_amount is not None:
            if limit_amount <= 0:
                raise ValueError("Limit amount must be greater than 0")
            category.limit_amount = limit_amount

        if rollover_excess is not None:
            category.rollover_excess = rollover_excess

        self.db.commit()
        self.db.refresh(category)
        return category

    def remove_category_from_budget(self, category_id: int) -> bool:
        """Remove a category from a budget.

        Args:
            category_id: BudgetCategory ID

        Returns:
            True if deleted, False if not found
        """
        category = self.db.execute(
            select(BudgetCategory).where(BudgetCategory.id == category_id)
        ).scalar_one_or_none()

        if not category:
            return False

        self.db.delete(category)
        self.db.commit()
        return True

    # ==================== BUDGET VS ACTUALS ====================

    def calculate_period_dates(
        self, period_type: str, reference_date: Optional[datetime] = None
    ) -> tuple[datetime, datetime]:
        """Calculate period start and end dates.

        Args:
            period_type: "monthly", "quarterly", or "annual"
            reference_date: Date to base period on (default: today UTC)

        Returns:
            Tuple of (period_start, period_end) as UTC datetime objects

        Raises:
            ValueError: If invalid period_type
        """
        if period_type not in [pt.value for pt in PeriodType]:
            raise ValueError(f"Invalid period_type: {period_type}")

        if reference_date is None:
            reference_date = datetime.now(timezone.utc)
        elif reference_date.tzinfo is None:
            reference_date = reference_date.replace(tzinfo=timezone.utc)

        year = reference_date.year
        month = reference_date.month

        if period_type == "monthly":
            period_start = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                period_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)

        elif period_type == "quarterly":
            quarter = (month - 1) // 3
            period_start = datetime(year, quarter * 3 + 1, 1, tzinfo=timezone.utc)
            if quarter == 3:
                period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                period_end = datetime(year, (quarter + 1) * 3 + 1, 1, tzinfo=timezone.utc)
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)

        else:  # annual
            period_start = datetime(year, 1, 1, tzinfo=timezone.utc)
            period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)

        return period_start, period_end

    def get_budget_vs_actuals(
        self, budget_id: int, period_start: datetime, period_end: datetime
    ) -> dict[str, Any]:
        """Calculate budget vs actual spending for a given period.

        Queries transactions in the date range, groups by category, calculates variance.

        Args:
            budget_id: Budget ID
            period_start: Period start (inclusive)
            period_end: Period end (inclusive)

        Returns:
            Dict with structure:
            {
                "budget_id": int,
                "currency": str,
                "period": {"start": str, "end": str},
                "categories": [
                    {
                        "category_id": int,
                        "category_name": str,
                        "limit": float,
                        "actual": float,
                        "variance": float,  # limit - actual (positive = under budget)
                        "percent": float,   # actual / limit * 100
                        "rollover_excess": bool,
                        "status": str,  # "under", "over", "ok" (ok = within 10%)
                    }
                ],
                "total": {
                    "limit": float,
                    "actual": float,
                    "variance": float,
                    "percent": float,
                }
            }

        Raises:
            ValueError: If budget not found
        """
        budget = self.get_budget(budget_id)
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")

        # Ensure UTC timezone on dates
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=timezone.utc)
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)

        # Get all transactions in period (expenses only)
        transactions = self.db.execute(
            select(Transaction).where(
                and_(
                    Transaction.date >= period_start,
                    Transaction.date <= period_end,
                    Transaction.type == TransactionType.EXPENSE,
                )
            )
        ).scalars().all()

        # Build actual spending by category
        actual_by_category: dict[str, Decimal] = {}
        for tx in transactions:
            category = tx.category or "Uncategorized"
            actual_by_category[category] = actual_by_category.get(category, Decimal(0)) + abs(
                tx.amount
            )

        # Build category results
        categories_result = []
        total_limit = Decimal(0)
        total_actual = Decimal(0)

        for bc in budget.categories:
            actual = actual_by_category.get(bc.category_name, Decimal(0))
            variance = bc.limit_amount - actual
            percent = float((actual / bc.limit_amount * 100)) if bc.limit_amount > 0 else 0

            # Determine status
            if actual > bc.limit_amount:
                status = "over"
            elif actual > bc.limit_amount * Decimal("0.9"):
                status = "ok"
            else:
                status = "under"

            categories_result.append(
                {
                    "category_id": bc.id,
                    "category_name": bc.category_name,
                    "limit": float(bc.limit_amount),
                    "actual": float(actual),
                    "variance": float(variance),
                    "percent": percent,
                    "rollover_excess": bc.rollover_excess,
                    "status": status,
                }
            )

            total_limit += bc.limit_amount
            total_actual += actual

        total_variance = total_limit - total_actual
        total_percent = float((total_actual / total_limit * 100)) if total_limit > 0 else 0

        return {
            "budget_id": budget_id,
            "currency": budget.currency,
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "categories": categories_result,
            "total": {
                "limit": float(total_limit),
                "actual": float(total_actual),
                "variance": float(total_variance),
                "percent": total_percent,
            },
        }

    def get_budget_with_tracking(
        self, budget_id: int, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get budget details with actual spending tracked for a date range.

        Args:
            budget_id: ID of the budget
            start_date: Period start date (inclusive)
            end_date: Period end date (inclusive)

        Returns:
            Dictionary containing:
            - budget: Budget metadata
            - period_start: Start of tracking period
            - period_end: End of tracking period
            - categories: List of budget categories with tracking data
            - summary: Total budget, actual, and variance
        """
        # Get the budget
        stmt = select(Budget).where(Budget.id == budget_id)
        budget = self.db.execute(stmt).scalars().first()
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")

        # Get all categories for this budget
        stmt = select(BudgetCategory).where(BudgetCategory.budget_id == budget_id)
        categories = self.db.execute(stmt).scalars().all()

        # For each category, calculate actual spending
        categories_data = []
        total_limit = Decimal("0.00")
        total_actual = Decimal("0.00")

        for category in categories:
            # Get transactions for this category in the date range
            stmt = select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.category == category.category_name,
                    Transaction.type == TransactionType.EXPENSE,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date,
                )
            )
            actual_spent = self.db.execute(stmt).scalar() or Decimal("0.00")

            # Ensure positive amount for expenses
            actual_spent = abs(actual_spent)

            # Calculate variance (negative = over budget)
            variance = category.limit_amount - actual_spent
            variance_pct = (
                (variance / category.limit_amount * 100).quantize(Decimal("0.01"))
                if category.limit_amount > 0
                else Decimal("0.00")
            )
            percent_used = (
                (actual_spent / category.limit_amount * 100).quantize(Decimal("0.01"))
                if category.limit_amount > 0
                else Decimal("0.00")
            )

            categories_data.append(
                {
                    "id": category.id,
                    "category_name": category.category_name,
                    "limit_amount": float(category.limit_amount),
                    "actual_spent": float(actual_spent),
                    "variance": float(variance),
                    "variance_pct": float(variance_pct),
                    "percent_used": float(percent_used),
                    "is_over_budget": actual_spent > category.limit_amount,
                }
            )

            total_limit += category.limit_amount
            total_actual += actual_spent

        # Calculate totals
        total_variance = total_limit - total_actual
        total_variance_pct = (
            (total_variance / total_limit * 100).quantize(Decimal("0.01"))
            if total_limit > 0
            else Decimal("0.00")
        )
        total_percent_used = (
            (total_actual / total_limit * 100).quantize(Decimal("0.01"))
            if total_limit > 0
            else Decimal("0.00")
        )

        return {
            "budget": {
                "id": budget.id,
                "name": budget.name,
                "currency": budget.currency,
                "description": budget.description,
                "is_active": budget.is_active,
            },
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "categories": sorted(
                categories_data, key=lambda x: x["variance"], reverse=False
            ),  # Sort by variance (largest overage first)
            "summary": {
                "total_limit": float(total_limit),
                "total_actual": float(total_actual),
                "total_variance": float(total_variance),
                "variance_pct": float(total_variance_pct),
                "percent_used": float(total_percent_used),
                "is_over_budget": total_actual > total_limit,
            },
        }

    def get_all_budgets(self) -> list[dict[str, Any]]:
        """Get all active budgets.

        Returns:
            List of budget summaries
        """
        stmt = select(Budget).where(Budget.is_active == True).order_by(Budget.name)
        budgets = self.db.execute(stmt).scalars().all()

        return [
            {
                "id": b.id,
                "name": b.name,
                "currency": b.currency,
                "description": b.description,
                "is_active": b.is_active,
                "created_at": b.created_at.isoformat(),
            }
            for b in budgets
        ]
