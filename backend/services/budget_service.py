"""Budget service for managing spending budgets and tracking.

Canopy - Personal Finance Platform
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.db.models.budget import Budget, BudgetCategory, BudgetPeriodType
from backend.db.models.transaction import Transaction as TransactionModel
from backend.models.budget_responses import (
    BudgetCategoryResponse,
    BudgetResponse,
    BudgetStatusResponse,
    CategoryStatusResponse,
    UpdateBudgetRequest,
)


class BudgetService:
    """Service for managing budgets and tracking spending."""

    def __init__(self, db: Session):
        """Initialize budget service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_budget(
        self,
        name: str,
        amount: Decimal,
        period: str,
        categories: Optional[list[dict[str, Any]]] = None,
    ) -> BudgetResponse:
        """Create a new budget with optional categories.

        Args:
            name: Budget name
            amount: Total budget amount
            period: Budget period ('monthly' or 'yearly')
            categories: Optional list of category dicts with 'category_name' and 'amount_limit'

        Returns:
            BudgetResponse with created budget and categories

        Raises:
            ValueError: If period is invalid or category data is malformed
        """
        # Validate period
        try:
            period_type = BudgetPeriodType(period)
        except ValueError:
            raise ValueError(
                f"Invalid period: {period}. Must be 'monthly' or 'yearly'"
            )

        # Create budget
        budget = Budget(
            name=name,
            amount=amount,
            period=period_type,
            active=True,
        )

        self.db.add(budget)
        self.db.flush()  # Get budget.id for categories

        # Add categories if provided
        category_responses = []
        if categories:
            for cat_data in categories:
                if "category_name" not in cat_data or "amount_limit" not in cat_data:
                    raise ValueError(
                        "Each category must have 'category_name' and 'amount_limit'"
                    )

                category = BudgetCategory(
                    budget_id=budget.id,
                    category_name=cat_data["category_name"],
                    amount_limit=Decimal(str(cat_data["amount_limit"])),
                )
                self.db.add(category)
                self.db.flush()

                category_responses.append(
                    BudgetCategoryResponse(
                        id=category.id,
                        category_name=category.category_name,
                        amount_limit=category.amount_limit,
                    )
                )

        self.db.commit()
        self.db.refresh(budget)

        return BudgetResponse(
            id=budget.id,
            name=budget.name,
            amount=budget.amount,
            period=budget.period.value,
            active=budget.active,
            categories=category_responses,
        )

    def get_budget(self, budget_id: int) -> Optional[BudgetResponse]:
        """Fetch budget with categories by ID.

        Args:
            budget_id: Budget ID

        Returns:
            BudgetResponse if found, None otherwise
        """
        query = (
            select(Budget)
            .where(Budget.id == budget_id)
            .options(joinedload(Budget.categories))
        )

        result = self.db.execute(query).scalars().first()

        if not result:
            return None

        category_responses = [
            BudgetCategoryResponse(
                id=cat.id,
                category_name=cat.category_name,
                amount_limit=cat.amount_limit,
            )
            for cat in result.categories
        ]

        return BudgetResponse(
            id=result.id,
            name=result.name,
            amount=result.amount,
            period=result.period.value,
            active=result.active,
            categories=category_responses,
        )

    def update_budget(
        self, budget_id: int, data: UpdateBudgetRequest
    ) -> Optional[BudgetResponse]:
        """Update budget details.

        Args:
            budget_id: Budget ID
            data: Update request with optional name, amount, active fields

        Returns:
            Updated BudgetResponse if found, None otherwise
        """
        query = select(Budget).where(Budget.id == budget_id)
        budget = self.db.execute(query).scalars().first()

        if not budget:
            return None

        # Update fields if provided
        if data.name is not None:
            budget.name = data.name
        if data.amount is not None:
            budget.amount = data.amount
        if data.active is not None:
            budget.active = data.active

        self.db.commit()
        self.db.refresh(budget)

        return self.get_budget(budget_id)

    def delete_budget(self, budget_id: int) -> bool:
        """Soft delete budget by setting active=False.

        Args:
            budget_id: Budget ID

        Returns:
            True if budget was found and deleted, False otherwise
        """
        query = select(Budget).where(Budget.id == budget_id)
        budget = self.db.execute(query).scalars().first()

        if not budget:
            return False

        budget.active = False
        self.db.commit()

        return True

    def list_budgets(self, active_only: bool = True) -> list[BudgetResponse]:
        """List all budgets.

        Args:
            active_only: If True, only return active budgets (default: True)

        Returns:
            List of BudgetResponse objects
        """
        query = select(Budget).options(joinedload(Budget.categories))

        if active_only:
            query = query.where(Budget.active)

        budgets = self.db.execute(query).scalars().all()

        return [
            BudgetResponse(
                id=budget.id,
                name=budget.name,
                amount=budget.amount,
                period=budget.period.value,
                active=budget.active,
                categories=[
                    BudgetCategoryResponse(
                        id=cat.id,
                        category_name=cat.category_name,
                        amount_limit=cat.amount_limit,
                    )
                    for cat in budget.categories
                ],
            )
            for budget in budgets
        ]

    def add_category(
        self, budget_id: int, category_name: str, amount_limit: Decimal
    ) -> Optional[BudgetCategoryResponse]:
        """Add a category to an existing budget.

        Args:
            budget_id: Budget ID
            category_name: Category name
            amount_limit: Category spending limit

        Returns:
            BudgetCategoryResponse if successful, None if budget not found

        Raises:
            ValueError: If category already exists for this budget
        """
        # Verify budget exists
        query = select(Budget).where(Budget.id == budget_id)
        budget = self.db.execute(query).scalars().first()

        if not budget:
            return None

        # Check if category already exists
        existing_query = select(BudgetCategory).where(
            BudgetCategory.budget_id == budget_id,
            BudgetCategory.category_name == category_name,
        )
        existing = self.db.execute(existing_query).scalars().first()

        if existing:
            raise ValueError(
                f"Category '{category_name}' already exists for budget {budget_id}"
            )

        # Create category
        category = BudgetCategory(
            budget_id=budget_id,
            category_name=category_name,
            amount_limit=amount_limit,
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        return BudgetCategoryResponse(
            id=category.id,
            category_name=category.category_name,
            amount_limit=category.amount_limit,
        )

    def track_spending(
        self, budget_id: int, period_start: date, period_end: date
    ) -> dict[str, Decimal]:
        """Calculate actual spending vs budget for a period.

        Args:
            budget_id: Budget ID
            period_start: Period start date
            period_end: Period end date

        Returns:
            Dictionary with spending breakdown by category and total

        Raises:
            ValueError: If budget not found
        """
        # Verify budget exists
        query = (
            select(Budget)
            .options(joinedload(Budget.categories))
            .where(Budget.id == budget_id)
        )
        budget = self.db.execute(query).scalars().first()

        if not budget:
            raise ValueError(f"Budget {budget_id} not found")

        # Query expense transactions in period
        tx_query = select(TransactionModel).where(
            TransactionModel.date >= period_start,
            TransactionModel.date <= period_end,
            TransactionModel.type == "expense",
        )

        transactions = self.db.execute(tx_query).scalars().all()

        # Calculate spending by category
        category_spending: dict[str, Decimal] = {}
        total_spent = Decimal("0.00")

        for tx in transactions:
            category = tx.category or "Uncategorized"
            amount = abs(tx.amount)

            category_spending[category] = (
                category_spending.get(category, Decimal("0.00")) + amount
            )
            total_spent += amount

        # Add total
        result = {"total": total_spent}
        result.update(category_spending)

        return result

    def get_budget_status(
        self, budget_id: int, month: Optional[str] = None
    ) -> Optional[BudgetStatusResponse]:
        """Get current period status with warnings.

        Args:
            budget_id: Budget ID
            month: Month in YYYY-MM format (defaults to current month)

        Returns:
            BudgetStatusResponse with status and category breakdowns, None if budget not found

        Raises:
            ValueError: If month format is invalid
        """
        # Parse month
        if month is None:
            today = date.today()
            month_str = f"{today.year}-{today.month:02d}"
        else:
            month_str = month

        try:
            year, month_num = map(int, month_str.split("-"))
        except ValueError:
            raise ValueError(
                f"Invalid month format: {month_str}. Expected YYYY-MM"
            )

        # Fetch budget
        query = (
            select(Budget)
            .options(joinedload(Budget.categories))
            .where(Budget.id == budget_id)
        )
        budget = self.db.execute(query).scalars().first()

        if not budget:
            return None

        # Calculate period dates based on budget type
        if budget.period == BudgetPeriodType.MONTHLY:
            period_start = date(year, month_num, 1)
            if month_num == 12:
                period_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(year, month_num + 1, 1) - timedelta(days=1)
        else:  # yearly
            period_start = date(year, 1, 1)
            period_end = date(year, 12, 31)

        # Get spending breakdown
        spending = self.track_spending(budget_id, period_start, period_end)
        total_spent = spending.pop("total")
        remaining = budget.amount - total_spent
        percentage_used = (
            float(total_spent / budget.amount * 100) if budget.amount > 0 else 0
        )

        # Determine overall status
        if percentage_used >= 100:
            status = "over"
        elif percentage_used >= 80:
            status = "warning"
        else:
            status = "under"

        # Build category status
        category_statuses = []
        for cat in budget.categories:
            cat_spent = spending.get(cat.category_name, Decimal("0.00"))
            cat_remaining = cat.amount_limit - cat_spent
            cat_percentage = (
                float(cat_spent / cat.amount_limit * 100)
                if cat.amount_limit > 0
                else 0
            )

            if cat_percentage >= 100:
                cat_status = "over"
            elif cat_percentage >= 80:
                cat_status = "warning"
            else:
                cat_status = "under"

            category_statuses.append(
                CategoryStatusResponse(
                    category_name=cat.category_name,
                    amount_limit=cat.amount_limit,
                    actual_spent=cat_spent,
                    remaining=cat_remaining,
                    percentage_used=cat_percentage,
                    status=cat_status,
                )
            )

        return BudgetStatusResponse(
            budget_id=budget.id,
            budget_name=budget.name,
            period_start=period_start,
            period_end=period_end,
            total_budget=budget.amount,
            total_spent=total_spent,
            remaining=remaining,
            percentage_used=percentage_used,
            status=status,
            categories=category_statuses,
            currency="CAD",
        )
