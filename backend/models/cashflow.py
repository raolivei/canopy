"""Pydantic models for Cashflow API.

Canopy - Personal Finance Platform
"""

from typing import Optional

from pydantic import BaseModel, Field


class MonthlySummary(BaseModel):
    """Monthly income, expenses, and net cashflow."""

    month: str = Field(..., description="Month in YYYY-MM format")
    income: float = Field(..., description="Total income for the month")
    expenses: float = Field(..., description="Total expenses for the month")
    net: float = Field(..., description="Net cashflow (income - expenses)")
    currency: str = Field(default="CAD", description="Currency code")


class MonthlySummaryRequest(BaseModel):
    """Request for monthly summary."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class MonthlySummaryResponse(BaseModel):
    """Response for monthly summary."""

    data: list[MonthlySummary]
    total_months: int = Field(..., description="Number of months in the summary")


class CashflowTrendRequest(BaseModel):
    """Request for cashflow trend."""

    months: int = Field(12, description="Number of months to analyze", ge=1, le=60)


class CashflowTrendResponse(BaseModel):
    """Response for cashflow trend."""

    months: int = Field(..., description="Number of months analyzed")
    monthly_data: list[MonthlySummary]
    average_income: float = Field(..., description="Average monthly income")
    average_expenses: float = Field(..., description="Average monthly expenses")
    average_net: float = Field(..., description="Average monthly net cashflow")
    trend: str = Field(
        ...,
        description="Overall trend: 'improving', 'declining', 'stable', or 'no_data'",
    )
    currency: str = Field(default="CAD", description="Currency code")


class CategoryBreakdownItem(BaseModel):
    """Category expense breakdown item."""

    category: str = Field(..., description="Expense category name")
    amount: float = Field(..., description="Total amount spent in category")
    percentage: float = Field(
        ..., description="Percentage of total expenses", ge=0, le=100
    )


class CategoryBreakdownRequest(BaseModel):
    """Request for category breakdown."""

    month: Optional[str] = Field(
        None, description="Month in YYYY-MM format (defaults to current month)"
    )


class CategoryBreakdownResponse(BaseModel):
    """Response for category breakdown."""

    month: str = Field(..., description="Month in YYYY-MM format")
    total_expenses: float = Field(..., description="Total expenses for the month")
    categories: list[CategoryBreakdownItem]
    currency: str = Field(default="CAD", description="Currency code")


class MonthlyBurn(BaseModel):
    """Monthly burn rate data point."""

    month: str = Field(..., description="Month in YYYY-MM format")
    amount: float = Field(..., description="Total expenses for the month")


class BurnRateRequest(BaseModel):
    """Request for burn rate calculation."""

    months: int = Field(3, description="Number of months to analyze", ge=1, le=24)


class BurnRateResponse(BaseModel):
    """Response for burn rate calculation."""

    months_analyzed: int = Field(..., description="Actual number of months with data")
    average_monthly_burn: float = Field(..., description="Average monthly spending")
    monthly_breakdown: list[MonthlyBurn]
    min_month: Optional[dict[str, float | str]] = Field(
        None, description="Month with minimum spending"
    )
    max_month: Optional[dict[str, float | str]] = Field(
        None, description="Month with maximum spending"
    )
    volatility: str = Field(
        ...,
        description="Spending volatility: 'low', 'moderate', 'high', or 'no_data'",
    )
    currency: str = Field(default="CAD", description="Currency code")
