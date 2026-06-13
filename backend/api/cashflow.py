"""Cashflow API endpoints for analyzing income, expenses, and savings trends.

Canopy - Personal Finance Platform
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.cashflow_service import CashflowService

router = APIRouter(prefix="/v1/cashflow", tags=["cashflow"])


# =============================================================================
# Response Models
# =============================================================================


class CategoryBreakdown(BaseModel):
    """Expense category breakdown."""

    category: str
    amount: float


class MonthlyMetricsResponse(BaseModel):
    """Monthly cashflow metrics response."""

    month: str
    income: float
    expenses: float
    savings: float
    savings_rate: float
    categories: list[CategoryBreakdown] = Field(default_factory=list)


class CashflowTrendResponse(BaseModel):
    """Cashflow trend response (multiple months)."""

    months: list[MonthlyMetricsResponse]


class CashflowSummaryResponse(BaseModel):
    """Cashflow summary response (date range)."""

    total_income: float
    total_expenses: float
    total_savings: float
    average_monthly_savings: float
    trend: str


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/monthly", response_model=MonthlyMetricsResponse, summary="Get monthly cashflow metrics")
def get_monthly_metrics(
    db: Session = Depends(get_db),
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g., 2026)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
):
    """Get cashflow metrics for a specific month (income, expenses, savings, top categories)."""
    service = CashflowService(db)
    metrics = service.get_monthly_metrics(year, month)
    return MonthlyMetricsResponse(
        month=metrics["month"],
        income=metrics["income"],
        expenses=metrics["expenses"],
        savings=metrics["savings"],
        savings_rate=metrics["savings_rate"],
        categories=[
            CategoryBreakdown(category=c["category"], amount=c["amount"])
            for c in metrics["categories"]
        ],
    )


@router.get(
    "/trend",
    response_model=CashflowTrendResponse,
    summary="Get cashflow trend for multiple months",
)
def get_cashflow_trend(
    db: Session = Depends(get_db),
    months: int = Query(12, ge=1, le=60, description="Number of months to include (default 12)"),
):
    """Get cashflow metrics for the last N months (trend analysis)."""
    service = CashflowService(db)
    trend = service.get_cashflow_trend(months)
    return CashflowTrendResponse(
        months=[
            MonthlyMetricsResponse(
                month=m["month"],
                income=m["income"],
                expenses=m["expenses"],
                savings=m["savings"],
                savings_rate=m["savings_rate"],
                categories=[
                    CategoryBreakdown(category=c["category"], amount=c["amount"])
                    for c in m["categories"]
                ],
            )
            for m in trend
        ]
    )


@router.get(
    "/summary",
    response_model=CashflowSummaryResponse,
    summary="Get cashflow summary for date range",
)
def get_cashflow_summary(
    db: Session = Depends(get_db),
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
):
    """Get aggregate cashflow summary for a date range (all-time stats)."""
    service = CashflowService(db)
    summary = service.get_cashflow_summary(start_date, end_date)
    return CashflowSummaryResponse(
        total_income=summary["total_income"],
        total_expenses=summary["total_expenses"],
        total_savings=summary["total_savings"],
        average_monthly_savings=summary["average_monthly_savings"],
        trend=summary["trend"],
    )
