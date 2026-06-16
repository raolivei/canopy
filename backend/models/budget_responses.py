"""Pydantic models for Budget API.

Canopy - Personal Finance Platform
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class BudgetCategoryResponse(BaseModel):
    """Budget category with spending limit."""

    id: int = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    amount_limit: Decimal = Field(..., description="Category spending limit")


class BudgetResponse(BaseModel):
    """Budget with categories."""

    id: int = Field(..., description="Budget ID")
    name: str = Field(..., description="Budget name")
    amount: Decimal = Field(..., description="Total budget amount")
    period: str = Field(..., description="Budget period: 'monthly' or 'yearly'")
    active: bool = Field(..., description="Whether budget is active")
    categories: list[BudgetCategoryResponse] = Field(
        default_factory=list, description="Category breakdowns"
    )


class CategoryStatusResponse(BaseModel):
    """Category spending status for a period."""

    category_name: str = Field(..., description="Category name")
    amount_limit: Decimal = Field(..., description="Category spending limit")
    actual_spent: Decimal = Field(..., description="Actual amount spent")
    remaining: Decimal = Field(..., description="Remaining budget")
    percentage_used: float = Field(..., description="Percentage of limit used", ge=0)
    status: str = Field(
        ...,
        description="Status: 'under', 'warning' (>80%), or 'over' (>100%)",
    )


class BudgetStatusResponse(BaseModel):
    """Budget status for a specific period."""

    budget_id: int = Field(..., description="Budget ID")
    budget_name: str = Field(..., description="Budget name")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    total_budget: Decimal = Field(..., description="Total budget amount")
    total_spent: Decimal = Field(..., description="Total amount spent")
    remaining: Decimal = Field(..., description="Remaining budget")
    percentage_used: float = Field(..., description="Percentage of budget used", ge=0)
    status: str = Field(
        ...,
        description="Overall status: 'under', 'warning', or 'over'",
    )
    categories: list[CategoryStatusResponse] = Field(
        default_factory=list, description="Category-level status"
    )
    currency: str = Field(default="CAD", description="Currency code")


class CreateBudgetRequest(BaseModel):
    """Request to create a new budget."""

    name: str = Field(..., description="Budget name", min_length=1, max_length=200)
    amount: Decimal = Field(..., description="Total budget amount", gt=0)
    period: str = Field(..., description="Budget period: 'monthly' or 'yearly'")
    categories: list[dict[str, str | Decimal]] = Field(
        default_factory=list,
        description="Category breakdowns with 'category_name' and 'amount_limit' keys",
    )


class UpdateBudgetRequest(BaseModel):
    """Request to update an existing budget."""

    name: Optional[str] = Field(
        None, description="Budget name", min_length=1, max_length=200
    )
    amount: Optional[Decimal] = Field(None, description="Total budget amount", gt=0)
    active: Optional[bool] = Field(None, description="Whether budget is active")


class AddCategoryRequest(BaseModel):
    """Request to add a category to a budget."""

    category_name: str = Field(
        ..., description="Category name", min_length=1, max_length=100
    )
    amount_limit: Decimal = Field(..., description="Category spending limit", gt=0)


class TrackSpendingRequest(BaseModel):
    """Request to track spending for a budget period."""

    budget_id: int = Field(..., description="Budget ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")


class BudgetStatusRequest(BaseModel):
    """Request to get budget status for a specific month."""

    budget_id: int = Field(..., description="Budget ID")
    month: Optional[str] = Field(
        None, description="Month in YYYY-MM format (defaults to current month)"
    )
