"""Pydantic models for Budget API requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class BudgetCategoryRequest(BaseModel):
    """Request model for adding a category to a budget."""

    category_name: str = Field(..., min_length=1, description="Category name from transaction system")
    limit_amount: Decimal = Field(..., gt=0, description="Monthly/period spending limit")
    period_type: str = Field(default="monthly", description="Period type: monthly, quarterly, annual")
    rollover_excess: bool = Field(default=False, description="Roll over unused budget to next period")


class BudgetCategoryTracking(BaseModel):
    """Tracking data for a budget category."""

    id: int
    category_name: str
    limit_amount: float
    actual_spent: float
    variance: float
    variance_pct: float
    percent_used: float
    is_over_budget: bool


class BudgetCategoryResponse(BaseModel):
    """Response model for a budget category with tracking info."""

    id: int
    budget_id: int
    category_name: str
    limit_amount: Decimal
    period_type: str
    rollover_excess: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetRequest(BaseModel):
    """Request model for creating/updating a budget."""

    name: str = Field(..., min_length=1, max_length=200, description="Budget name")
    currency: str = Field(default="CAD", description="Currency code (e.g., CAD, USD)")
    description: Optional[str] = Field(None, description="Budget description")


class BudgetUpdateRequest(BaseModel):
    """Request model for updating a budget."""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate budget")


class BudgetMetadata(BaseModel):
    """Budget metadata."""

    id: int
    name: str
    currency: str
    description: Optional[str]
    is_active: bool


class BudgetSummary(BaseModel):
    """Budget tracking summary."""

    total_limit: float
    total_actual: float
    total_variance: float
    variance_pct: float
    percent_used: float
    is_over_budget: bool


class BudgetResponse(BaseModel):
    """Response model for a budget with its categories."""

    id: int
    name: str
    currency: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    categories: List[BudgetCategoryResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class BudgetTrackingResponse(BaseModel):
    """Response model for budget vs actuals tracking."""

    budget: BudgetMetadata
    period_start: str  # ISO date string
    period_end: str  # ISO date string
    categories: List[BudgetCategoryTracking]
    summary: BudgetSummary

    class Config:
        from_attributes = True


class BudgetListResponse(BaseModel):
    """Response model for list of budgets."""

    id: int
    name: str
    currency: str
    description: Optional[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
