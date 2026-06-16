"""Pydantic models for Budget API request/response."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BudgetPeriodType(str, Enum):
    """Period type for budget recurrence."""

    MONTHLY = "monthly"
    YEARLY = "yearly"


class BudgetCategoryBase(BaseModel):
    """Base model for budget category."""

    category_name: str = Field(..., max_length=100)
    amount_limit: float = Field(..., gt=0)


class BudgetCategoryCreate(BudgetCategoryBase):
    """Request model for creating a budget category."""

    pass


class BudgetCategory(BudgetCategoryBase):
    """Response model for budget category."""

    id: int
    budget_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    """Request model for creating a budget."""

    name: str = Field(..., max_length=200)
    amount: float = Field(..., gt=0)
    period: BudgetPeriodType = BudgetPeriodType.MONTHLY
    user_id: Optional[int] = None
    categories: list[BudgetCategoryCreate] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    """Request model for updating a budget."""

    name: Optional[str] = Field(None, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    period: Optional[BudgetPeriodType] = None
    active: Optional[bool] = None


class Budget(BaseModel):
    """Response model for budget."""

    id: int
    name: str
    amount: float
    period: BudgetPeriodType
    user_id: Optional[int] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    categories: list[BudgetCategory] = Field(default_factory=list)

    class Config:
        from_attributes = True


class BudgetStatus(BaseModel):
    """Budget status for current period."""

    budget_id: int
    budget_name: str
    budget_amount: float
    period: BudgetPeriodType
    period_start: date
    period_end: date
    actual_spent: float
    remaining: float
    percentage_used: float
    is_over_budget: bool


class CategorySpending(BaseModel):
    """Category-level spending within a budget."""

    category_name: str
    amount_limit: float
    actual_spent: float
    remaining: float
    percentage_used: float
    is_over_budget: bool


class BudgetTracking(BaseModel):
    """Detailed budget tracking with category breakdown."""

    budget_id: int
    budget_name: str
    budget_amount: float
    period: BudgetPeriodType
    period_start: date
    period_end: date
    total_spent: float
    total_remaining: float
    percentage_used: float
    is_over_budget: bool
    categories: list[CategorySpending] = Field(default_factory=list)
