"""Insights API endpoints for Canopy (CAD-only, Canadian investments).

Provides endpoints for:
- Net worth summary (CAD)
- Asset allocation (by type, country, institution)
- FIRE calculations
- Projections
- Historical data
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.fire_calculator import FIRECalculator, get_fire_summary
from backend.services.insights_calculator import (
    InsightsCalculator,
    get_insights_summary,
)

router = APIRouter(prefix="/v1/insights", tags=["insights"])


# =============================================================================
# Response Models
# =============================================================================


class NetWorthResponse(BaseModel):
    """Net worth summary response (CAD)."""

    total_cad: float
    total_assets_cad: float
    total_liabilities_cad: float
    liquid_assets_cad: float
    investment_assets_cad: float
    retirement_assets_cad: float
    real_estate_equity_cad: float
    change_1d: Optional[float] = None
    change_1d_percent: Optional[float] = None
    change_1m: Optional[float] = None
    change_1m_percent: Optional[float] = None
    change_ytd: Optional[float] = None
    change_ytd_percent: Optional[float] = None


class AllocationResponse(BaseModel):
    """Asset allocation response (percentages)."""

    by_type: dict[str, float]
    by_country: dict[str, float]
    by_institution: dict[str, float]


class GrowthResponse(BaseModel):
    """Growth metrics response."""

    monthly_rate: float
    yearly_rate: float
    average_monthly: float
    best_month: Optional[str] = None
    best_month_return: Optional[float] = None
    worst_month: Optional[str] = None
    worst_month_return: Optional[float] = None


class InsightsSummaryResponse(BaseModel):
    """Complete insights summary response."""

    net_worth: NetWorthResponse
    allocation: AllocationResponse
    growth: GrowthResponse


class FIREMetricsResponse(BaseModel):
    """FIRE calculation metrics response (CAD)."""

    fire_number: float
    current_net_worth: float
    progress_percentage: float
    years_to_fire: Optional[float] = None
    fire_date: Optional[str] = None
    monthly_income_at_fire: float
    annual_income_at_fire: float
    monthly_expenses: float
    annual_expenses: float
    safe_withdrawal_rate: float
    expected_return: float
    return_assumption_source: str = "default"
    historical_annual_return_pct: Optional[float] = None
    historical_data_span_days: Optional[int] = None


class ProjectionPointResponse(BaseModel):
    year: int
    date: str
    net_worth: float
    contributions: float
    growth: float
    passive_income: float


class ScenarioResponse(BaseModel):
    name: str
    years_to_fire: Optional[float] = None
    fire_date: Optional[str] = None
    final_net_worth: float
    difference_years: Optional[float] = None


class FIRESummaryResponse(BaseModel):
    metrics: FIREMetricsResponse
    projections: list[ProjectionPointResponse]
    scenarios: list[ScenarioResponse]


class FIRECalculationRequest(BaseModel):
    """Request body for custom FIRE calculations (CAD)."""

    monthly_expenses: float = Field(default=5000, description="Monthly expenses in CAD")
    monthly_savings: float = Field(default=2000, description="Monthly savings in CAD")
    safe_withdrawal_rate: float = Field(
        default=0.04, description="Safe withdrawal rate (e.g., 0.04 for 4%)"
    )
    expected_return: float = Field(
        default=0.07, description="Expected annual return (e.g., 0.07 for 7%)"
    )


class HistoricalDataPoint(BaseModel):
    date: str
    net_worth: float
    cost_basis: Optional[float] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/summary", response_model=InsightsSummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    """Get complete insights summary (CAD)."""
    summary = get_insights_summary(db)
    return InsightsSummaryResponse(
        net_worth=NetWorthResponse(**summary["net_worth"]),
        allocation=AllocationResponse(**summary["allocation"]),
        growth=GrowthResponse(**summary["growth"]),
    )


@router.get("/net-worth", response_model=NetWorthResponse)
def get_net_worth(db: Session = Depends(get_db)):
    """Get net worth summary (CAD)."""
    calculator = InsightsCalculator(db)
    net_worth = calculator.calculate_net_worth()

    def _f(v: Optional[Decimal]) -> Optional[float]:
        return float(v) if v is not None else None

    return NetWorthResponse(
        total_cad=float(net_worth.net_worth_cad),
        total_assets_cad=float(net_worth.total_assets_cad),
        total_liabilities_cad=float(net_worth.total_liabilities_cad),
        liquid_assets_cad=float(net_worth.liquid_assets_cad),
        investment_assets_cad=float(net_worth.investment_assets_cad),
        retirement_assets_cad=float(net_worth.retirement_assets_cad),
        real_estate_equity_cad=float(net_worth.real_estate_equity_cad),
        change_1d=_f(net_worth.change_1d),
        change_1d_percent=_f(net_worth.change_1d_percent),
        change_1m=_f(net_worth.change_1m),
        change_1m_percent=_f(net_worth.change_1m_percent),
        change_ytd=_f(net_worth.change_ytd),
        change_ytd_percent=_f(net_worth.change_ytd_percent),
    )


@router.get("/allocation", response_model=AllocationResponse)
def get_allocation(db: Session = Depends(get_db)):
    calculator = InsightsCalculator(db)
    allocation = calculator.calculate_allocation()
    return AllocationResponse(
        by_type={k: float(v) for k, v in allocation.by_type.items()},
        by_country={k: float(v) for k, v in allocation.by_country.items()},
        by_institution={k: float(v) for k, v in allocation.by_institution.items()},
    )


@router.get("/growth", response_model=GrowthResponse)
def get_growth_metrics(db: Session = Depends(get_db)):
    calculator = InsightsCalculator(db)
    growth = calculator.calculate_growth_metrics()
    return GrowthResponse(
        monthly_rate=float(growth.monthly_growth_rate),
        yearly_rate=float(growth.yearly_growth_rate),
        average_monthly=float(growth.average_monthly_growth),
        best_month=growth.best_month.isoformat() if growth.best_month else None,
        best_month_return=float(growth.best_month_return)
        if growth.best_month_return
        else None,
        worst_month=growth.worst_month.isoformat() if growth.worst_month else None,
        worst_month_return=float(growth.worst_month_return)
        if growth.worst_month_return
        else None,
    )


@router.get("/historical", response_model=list[HistoricalDataPoint])
def get_historical_data(
    period: str = Query(default="1y", description="Period: 7d, 30d, 90d, 1y, all"),
    db: Session = Depends(get_db),
):
    calculator = InsightsCalculator(db)
    data = calculator.get_historical_net_worth(period=period)
    return [HistoricalDataPoint(**point) for point in data]


@router.get("/fire", response_model=FIRESummaryResponse)
def get_fire_metrics(
    monthly_expenses: float = Query(default=5000),
    monthly_savings: float = Query(default=2000),
    use_historical_return: bool = Query(
        default=False,
        description="If true, use CAGR from portfolio_snapshots (≥60d span) as expected return when available.",
    ),
    db: Session = Depends(get_db),
):
    """Get FIRE calculation summary (CAD)."""
    summary = get_fire_summary(
        db,
        monthly_expenses=Decimal(str(monthly_expenses)),
        monthly_savings=Decimal(str(monthly_savings)),
        use_historical_return=use_historical_return,
    )
    return FIRESummaryResponse(
        metrics=FIREMetricsResponse(**summary["metrics"]),
        projections=[ProjectionPointResponse(**p) for p in summary["projections"]],
        scenarios=[ScenarioResponse(**s) for s in summary["scenarios"]],
    )


@router.post("/fire/calculate", response_model=FIRESummaryResponse)
def calculate_fire(request: FIRECalculationRequest, db: Session = Depends(get_db)):
    """Calculate FIRE metrics with custom parameters (CAD)."""
    calculator = InsightsCalculator(db)
    net_worth = calculator.calculate_net_worth()

    fire_calc = FIRECalculator(db)
    metrics = fire_calc.calculate_fire_metrics(
        current_net_worth=net_worth.net_worth_cad,
        monthly_expenses=Decimal(str(request.monthly_expenses)),
        monthly_savings=Decimal(str(request.monthly_savings)),
        safe_withdrawal_rate=Decimal(str(request.safe_withdrawal_rate)),
        expected_return=Decimal(str(request.expected_return)),
    )

    projections = fire_calc.project_net_worth(
        current_net_worth=net_worth.net_worth_cad,
        monthly_savings=Decimal(str(request.monthly_savings)),
        years=30,
        annual_return=Decimal(str(request.expected_return)),
        safe_withdrawal_rate=Decimal(str(request.safe_withdrawal_rate)),
    )

    exp_ret = Decimal(str(request.expected_return))
    scenarios = fire_calc.run_what_if_scenarios(
        current_net_worth=net_worth.net_worth_cad,
        monthly_expenses=Decimal(str(request.monthly_expenses)),
        monthly_savings=Decimal(str(request.monthly_savings)),
        baseline_annual_return=exp_ret,
    )

    return FIRESummaryResponse(
        metrics=FIREMetricsResponse(
            fire_number=float(metrics.fire_number),
            current_net_worth=float(metrics.current_net_worth),
            progress_percentage=float(metrics.progress_percentage),
            years_to_fire=metrics.years_to_fire,
            fire_date=metrics.fire_date.isoformat() if metrics.fire_date else None,
            monthly_income_at_fire=float(metrics.monthly_income_at_fire),
            annual_income_at_fire=float(metrics.annual_income_at_fire),
            monthly_expenses=float(metrics.monthly_expenses),
            annual_expenses=float(metrics.annual_expenses),
            safe_withdrawal_rate=float(metrics.safe_withdrawal_rate),
            expected_return=float(metrics.expected_return),
            return_assumption_source="custom",
        ),
        projections=[
            ProjectionPointResponse(
                year=p.year,
                date=p.date.isoformat(),
                net_worth=float(p.net_worth),
                contributions=float(p.contributions),
                growth=float(p.growth),
                passive_income=float(p.passive_income),
            )
            for p in projections
        ],
        scenarios=[
            ScenarioResponse(
                name=s.name,
                years_to_fire=s.years_to_fire,
                fire_date=s.fire_date.isoformat() if s.fire_date else None,
                final_net_worth=float(s.final_net_worth),
                difference_years=s.difference_years,
            )
            for s in scenarios
        ],
    )


@router.get("/projections", response_model=list[ProjectionPointResponse])
def get_projections(
    current_net_worth: Optional[float] = Query(default=None),
    monthly_savings: float = Query(default=2000),
    years: int = Query(default=30),
    annual_return: float = Query(default=0.07),
    db: Session = Depends(get_db),
):
    if current_net_worth is None:
        calculator = InsightsCalculator(db)
        net_worth = calculator.calculate_net_worth()
        current_net_worth = float(net_worth.net_worth_cad)

    fire_calc = FIRECalculator(db)
    projections = fire_calc.project_net_worth(
        current_net_worth=Decimal(str(current_net_worth)),
        monthly_savings=Decimal(str(monthly_savings)),
        years=years,
        annual_return=Decimal(str(annual_return)),
    )

    return [
        ProjectionPointResponse(
            year=p.year,
            date=p.date.isoformat(),
            net_worth=float(p.net_worth),
            contributions=float(p.contributions),
            growth=float(p.growth),
            passive_income=float(p.passive_income),
        )
        for p in projections
    ]
