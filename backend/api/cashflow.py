"""Cashflow API endpoints for income, expenses, and burn rate analysis."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.db.session import DbSession
from backend.models.cashflow import (
    CategoryBreakdownResponse,
    BurnRateResponse,
    CashflowTrendResponse,
    MonthlySummaryResponse,
    MonthlySummary,
)
from backend.services.cashflow_service import CashflowService

router = APIRouter(prefix="/v1/cashflow", tags=["cashflow"])


@router.get("/summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    db: DbSession,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
):
    """Get monthly income, expenses, and net cashflow for a date range.

    Args:
        db: Database session
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Monthly summary data with income, expenses, and net for each month
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid date format: {str(e)}"
        ) from e

    if start > end:
        raise HTTPException(
            status_code=400, detail="Start date must be before or equal to end date"
        )

    service = CashflowService(db)
    monthly_data = service.get_monthly_summary(start, end)

    return MonthlySummaryResponse(
        data=[MonthlySummary(**m) for m in monthly_data],
        total_months=len(monthly_data),
    )


@router.get("/trend", response_model=CashflowTrendResponse)
async def get_cashflow_trend(
    db: DbSession,
    months: int = Query(12, ge=1, le=60, description="Number of months to analyze"),
):
    """Get cashflow trend analysis over N months.

    Calculates average income, expenses, and net cashflow, and determines
    if the trend is improving, declining, or stable.

    Args:
        db: Database session
        months: Number of months to analyze (default: 12, max: 60)

    Returns:
        Cashflow trend data with monthly breakdown and trend analysis
    """
    service = CashflowService(db)
    trend_data = service.get_cashflow_trend(months)

    return CashflowTrendResponse(
        months=trend_data["months"],
        monthly_data=[MonthlySummary(**m) for m in trend_data["monthly_data"]],
        average_income=trend_data["average_income"],
        average_expenses=trend_data["average_expenses"],
        average_net=trend_data["average_net"],
        trend=trend_data["trend"],
        currency=trend_data["currency"],
    )


@router.get("/categories", response_model=CategoryBreakdownResponse)
async def get_category_breakdown(
    db: DbSession,
    month: Optional[str] = Query(
        None, description="Month in YYYY-MM format (defaults to current month)"
    ),
):
    """Get expense breakdown by category for a specific month.

    Shows total expenses and percentage breakdown for each spending category.

    Args:
        db: Database session
        month: Month in YYYY-MM format (defaults to current month)

    Returns:
        Category breakdown with amounts and percentages
    """
    if month is not None:
        try:
            # Validate month format
            datetime.strptime(month, "%Y-%m")
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid month format: {str(e)}"
            ) from e

    service = CashflowService(db)
    breakdown_data = service.get_category_breakdown(month)

    return CategoryBreakdownResponse(**breakdown_data)


@router.get("/burn-rate", response_model=BurnRateResponse)
async def get_burn_rate(
    db: DbSession,
    months: int = Query(3, ge=1, le=24, description="Number of months to analyze"),
):
    """Calculate average monthly spending (burn rate).

    Analyzes spending patterns over N months to determine average monthly
    expenses, volatility, and min/max spending months.

    Args:
        db: Database session
        months: Number of months to analyze (default: 3, max: 24)

    Returns:
        Burn rate metrics including average monthly spending and volatility
    """
    service = CashflowService(db)
    burn_data = service.calculate_burn_rate(months)

    return BurnRateResponse(**burn_data)
