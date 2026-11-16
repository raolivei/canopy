"""Budget CRUD and period status on the shared calculation contract.

Budgets are kept in CAD (there is no currency column). Spending is aggregated
per original currency; non-CAD spend is converted at the period-end rate
when one exists and otherwise reported as unconverted, never guessed.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from backend.db.models.budget import Budget, BudgetCategory, BudgetPeriodType
from backend.models.budget import BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCreate, BudgetUpdate
from backend.services.calculation import (
    ZERO,
    CurrencyFlow,
    bucket_by_category,
    month_bounds,
    monthly_flows,
    parse_month,
    quantize,
    rate_lookup,
    to_reporting,
    year_bounds,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

BUDGET_CURRENCY = "CAD"
WARNING_THRESHOLD = 80.0


class BudgetNotFound(LookupError):
    """No budget with that id."""


class CategoryNotFound(LookupError):
    """No category with that id on that budget."""


class DuplicateCategory(ValueError):
    """The budget already has a category with that name."""


def _health(percentage_used: float) -> str:
    if percentage_used >= 100:
        return "over"
    if percentage_used >= WARNING_THRESHOLD:
        return "warning"
    return "under"


def _flow_dict(flow: CurrencyFlow) -> dict[str, Decimal]:
    q = flow.quantized()
    return {"income": q.income, "expenses": q.expenses, "net": q.net}


class BudgetService:
    """Single path for budget CRUD and status; the router only maps errors to HTTP."""

    def __init__(self, db: Session):
        self.db = db
        self._rate_on = rate_lookup(db)

    # ------------------------------------------------------------------ CRUD

    def _load(self, budget_id: int) -> Budget:
        budget = self.db.execute(
            select(Budget).options(selectinload(Budget.categories)).where(Budget.id == budget_id)
        ).scalar_one_or_none()
        if budget is None:
            raise BudgetNotFound(f"Budget {budget_id} not found")
        return budget

    def list_budgets(self, *, active_only: bool = True) -> Sequence[Budget]:
        stmt = (
            select(Budget).options(selectinload(Budget.categories)).order_by(Budget.created_at.desc(), Budget.id.desc())
        )
        if active_only:
            stmt = stmt.where(Budget.active.is_(True))
        return self.db.execute(stmt).scalars().all()

    def get_budget(self, budget_id: int) -> Budget:
        return self._load(budget_id)

    def create_budget(self, data: BudgetCreate) -> Budget:
        names = [c.category_name for c in data.categories]
        if len(names) != len(set(names)):
            raise DuplicateCategory("Category names must be unique within a budget")
        budget = Budget(name=data.name, amount=data.amount, period=data.period, active=True)
        budget.categories = [
            BudgetCategory(category_name=c.category_name, amount_limit=c.amount_limit) for c in data.categories
        ]
        self.db.add(budget)
        self.db.commit()
        return self._load(budget.id)

    def update_budget(self, budget_id: int, data: BudgetUpdate) -> Budget:
        budget = self._load(budget_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(budget, field, value)
        self.db.commit()
        return self._load(budget_id)

    def delete_budget(self, budget_id: int) -> None:
        """Soft delete: the budget stays for history but drops out of active lists."""
        budget = self._load(budget_id)
        budget.active = False
        self.db.commit()

    def add_category(self, budget_id: int, data: BudgetCategoryCreate) -> BudgetCategory:
        budget = self._load(budget_id)
        if any(c.category_name == data.category_name for c in budget.categories):
            raise DuplicateCategory(f"Category '{data.category_name}' already exists on budget {budget_id}")
        category = BudgetCategory(budget_id=budget_id, category_name=data.category_name, amount_limit=data.amount_limit)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def _load_category(self, budget_id: int, category_id: int) -> BudgetCategory:
        budget = self._load(budget_id)
        for category in budget.categories:
            if category.id == category_id:
                return category
        raise CategoryNotFound(f"Category {category_id} not found on budget {budget_id}")

    def update_category(self, budget_id: int, category_id: int, data: BudgetCategoryUpdate) -> BudgetCategory:
        category = self._load_category(budget_id, category_id)
        changes = data.model_dump(exclude_unset=True)
        new_name = changes.get("category_name")
        if new_name and any(c.category_name == new_name and c.id != category_id for c in category.budget.categories):
            raise DuplicateCategory(f"Category '{new_name}' already exists on budget {budget_id}")
        for field, value in changes.items():
            setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, budget_id: int, category_id: int) -> None:
        category = self._load_category(budget_id, category_id)
        self.db.delete(category)
        self.db.commit()

    # ---------------------------------------------------------------- status

    @staticmethod
    def period_bounds_for(budget: Budget, year: int, month: int) -> tuple[date, date]:
        """Half-open bounds of the budget period containing ``year``/``month``."""
        if budget.period == BudgetPeriodType.YEARLY:
            return year_bounds(year)
        return month_bounds(year, month)

    def track_spending(self, start: date, end_exclusive: date) -> dict[str, dict[str, CurrencyFlow]]:
        """Expense totals per category and currency in ``[start, end_exclusive)``."""
        rows = [r for r in monthly_flows(self.db, start, end_exclusive, by_category=True) if r.kind == "expense"]
        return bucket_by_category(rows)

    def get_budget_status(
        self, budget_id: int, month: str | None = None, *, today: date | None = None
    ) -> dict[str, Any]:
        """Spend against the budget for the period containing ``month`` (default: today's month)."""
        today = today or date.today()
        year, month_num = parse_month(month) if month else (today.year, today.month)
        budget = self._load(budget_id)
        start, end_exclusive = self.period_bounds_for(budget, year, month_num)
        as_of = end_exclusive - timedelta(days=1)

        spending = self.track_spending(start, end_exclusive)

        all_flows: dict[str, CurrencyFlow] = {}
        for flows in spending.values():
            for currency, flow in flows.items():
                all_flows.setdefault(currency, CurrencyFlow()).expenses += flow.expenses
        totals = to_reporting(all_flows, BUDGET_CURRENCY, self._rate_on, as_of)
        total_spent = totals.expenses
        total_budget = quantize(budget.amount)
        pct = float(total_spent / total_budget * 100) if total_budget > 0 else 0.0

        categories = []
        for category in sorted(budget.categories, key=lambda c: c.category_name.lower()):
            flows = spending.get(category.category_name, {})
            cat_totals = to_reporting(flows, BUDGET_CURRENCY, self._rate_on, as_of)
            limit = quantize(category.amount_limit)
            cat_pct = float(cat_totals.expenses / limit * 100) if limit > 0 else 0.0
            categories.append(
                {
                    "category_id": category.id,
                    "category_name": category.category_name,
                    "amount_limit": limit,
                    "actual_spent": cat_totals.expenses,
                    "remaining": limit - cat_totals.expenses,
                    "percentage_used": cat_pct,
                    "status": _health(cat_pct),
                    "by_currency": {ccy: _flow_dict(f) for ccy, f in sorted(flows.items())},
                    "fx_complete": cat_totals.fx_complete,
                    "unconverted": {ccy: _flow_dict(f) for ccy, f in sorted(cat_totals.unconverted.items())},
                }
            )

        return {
            "budget_id": budget.id,
            "budget_name": budget.name,
            "period": budget.period,
            "period_start": start,
            "period_end": as_of,
            "currency": BUDGET_CURRENCY,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining": total_budget - total_spent,
            "percentage_used": pct,
            "status": _health(pct),
            "fx_complete": totals.fx_complete,
            "spent_by_currency": {ccy: _flow_dict(f) for ccy, f in sorted(all_flows.items())},
            "unconverted": {ccy: _flow_dict(f) for ccy, f in sorted(totals.unconverted.items())},
            "fx": [
                {
                    "from_currency": p.from_currency,
                    "to_currency": p.to_currency,
                    "pair": p.pair,
                    "rate": p.rate,
                    "as_of": p.as_of,
                    "source": p.source,
                }
                for p in totals.fx
            ],
            "categories": categories,
        }


__all__ = [
    "BUDGET_CURRENCY",
    "ZERO",
    "BudgetNotFound",
    "BudgetService",
    "CategoryNotFound",
    "DuplicateCategory",
]
