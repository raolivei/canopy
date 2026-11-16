"""Cash-flow API: monthly summary, trend, category breakdown, burn rate, period comparison."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from backend.db.session import DbSession
from backend.models.cashflow import (
    BurnRateResponse,
    CashflowTrendResponse,
    CategoryBreakdownResponse,
    ComparisonResponse,
    FlowKind,
    MonthlySummaryResponse,
    PeriodKind,
    ReportingCurrency,
)
from backend.services.calculation import parse_month
from backend.services.cashflow_service import CashflowService

router = APIRouter(prefix="/v1/cashflow", tags=["cashflow"])

ReportingQuery = Query("CAD", description="Currency every total is expressed in")


def _parse_date(value: str, name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {name}: expected YYYY-MM-DD") from exc


def _validate_month(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        parse_month(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return value


@router.get("/summary", response_model=MonthlySummaryResponse)
def get_monthly_summary(
    db: DbSession,
    start_date: str = Query(..., description="YYYY-MM-DD, inclusive"),
    end_date: str = Query(..., description="YYYY-MM-DD, inclusive"),
    reporting_currency: ReportingCurrency = ReportingQuery,
) -> MonthlySummaryResponse:
    """Income, expenses and net per calendar month; months without data are zero-filled."""
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")
    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

    data = CashflowService(db, reporting_currency).get_monthly_summary(start, end)
    return MonthlySummaryResponse(
        data=data,
        total_months=len(data),
        currency=reporting_currency,
        fx_complete=all(m["fx_complete"] for m in data),
    )


@router.get("/trend", response_model=CashflowTrendResponse)
def get_cashflow_trend(
    db: DbSession,
    months: int = Query(12, ge=1, le=60, description="Calendar months including the current one"),
    reporting_currency: ReportingCurrency = ReportingQuery,
) -> CashflowTrendResponse:
    """Monthly data for the trailing window with averages and a trend label."""
    return CashflowTrendResponse(**CashflowService(db, reporting_currency).get_cashflow_trend(months))


@router.get("/categories", response_model=CategoryBreakdownResponse)
def get_category_breakdown(
    db: DbSession,
    month: str | None = Query(None, description="YYYY-MM (defaults to the current month)"),
    kind: FlowKind = Query("expense", description="Which flows to break down"),
    reporting_currency: ReportingCurrency = ReportingQuery,
) -> CategoryBreakdownResponse:
    """Totals per category for one month."""
    month = _validate_month(month)
    return CategoryBreakdownResponse(**CashflowService(db, reporting_currency).get_category_breakdown(month, kind=kind))


@router.get("/burn-rate", response_model=BurnRateResponse)
def get_burn_rate(
    db: DbSession,
    months: int = Query(3, ge=1, le=24, description="Calendar months including the current one"),
    reporting_currency: ReportingCurrency = ReportingQuery,
) -> BurnRateResponse:
    """Average monthly spending and its volatility over the window."""
    return BurnRateResponse(**CashflowService(db, reporting_currency).calculate_burn_rate(months))


@router.get("/comparison", response_model=ComparisonResponse)
def get_comparison(
    db: DbSession,
    kind: PeriodKind = Query("month", description="Period kind to compare"),
    reference: str | None = Query(None, description="YYYY-MM inside the current period (defaults to today)"),
    reporting_currency: ReportingCurrency = ReportingQuery,
) -> ComparisonResponse:
    """The period containing ``reference`` versus the one before it."""
    reference = _validate_month(reference)
    return ComparisonResponse(**CashflowService(db, reporting_currency).get_comparison(kind, reference))
