"""Pydantic schemas for the budget API (single source for requests and responses)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.db.models.budget import BudgetPeriodType
from backend.models.cashflow import CurrencyFlowOut, FxProvenanceOut
from backend.models.money import Money

BudgetHealth = Literal["under", "warning", "over"]


class BudgetCategoryCreate(BaseModel):
    category_name: str = Field(min_length=1, max_length=100)
    amount_limit: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class BudgetCategoryUpdate(BaseModel):
    category_name: str | None = Field(None, min_length=1, max_length=100)
    amount_limit: Decimal | None = Field(None, gt=0, max_digits=18, decimal_places=2)


class BudgetCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    budget_id: int
    category_name: str
    amount_limit: Money
    created_at: datetime
    updated_at: datetime


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    period: BudgetPeriodType = BudgetPeriodType.MONTHLY
    categories: list[BudgetCategoryCreate] = Field(default_factory=list)


class BudgetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    amount: Decimal | None = Field(None, gt=0, max_digits=18, decimal_places=2)
    period: BudgetPeriodType | None = None
    active: bool | None = None


class Budget(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: Money
    currency: str = Field("CAD", description="Budgets are kept in CAD")
    period: BudgetPeriodType
    active: bool
    created_at: datetime
    updated_at: datetime
    categories: list[BudgetCategory] = Field(default_factory=list)


class CategoryStatus(BaseModel):
    category_id: int
    category_name: str
    amount_limit: Money
    actual_spent: Money
    remaining: Money
    percentage_used: float = Field(ge=0)
    status: BudgetHealth
    by_currency: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    fx_complete: bool
    unconverted: dict[str, CurrencyFlowOut] = Field(default_factory=dict)


class BudgetStatus(BaseModel):
    budget_id: int
    budget_name: str
    period: BudgetPeriodType
    period_start: date
    period_end: date = Field(description="Last day of the period (inclusive)")
    currency: str
    total_budget: Money
    total_spent: Money = Field(description="All expense spend in the period, in the budget currency")
    remaining: Money
    percentage_used: float = Field(ge=0)
    status: BudgetHealth
    fx_complete: bool
    spent_by_currency: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    unconverted: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    fx: list[FxProvenanceOut] = Field(default_factory=list)
    categories: list[CategoryStatus] = Field(default_factory=list)
