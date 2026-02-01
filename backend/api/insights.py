"""Insights API endpoints for Canopy.

Canopy - Personal Finance Platform

Provides endpoints for:
- Net worth summary
- Asset allocation
- Currency exposure
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
from backend.services.insights_calculator import (
    InsightsCalculator,
    get_insights_summary,
)
from backend.services.fire_calculator import (
    FIRECalculator,
    get_fire_summary,
)


router = APIRouter(prefix="/v1/insights", tags=["insights"])


# =============================================================================
# Request/Response Models
# =============================================================================

class NetWorthResponse(BaseModel):
    """Net worth summary response."""
    total_usd: float
    total_assets_usd: float
    total_liabilities_usd: float
    liquid_assets_usd: float
    investment_assets_usd: float
    retirement_assets_usd: float
    real_estate_equity_usd: float
    assets_by_currency: dict[str, float]
    liabilities_by_currency: dict[str, float]
    change_1d: Optional[float] = None
    change_1d_percent: Optional[float] = None
    change_1m: Optional[float] = None
    change_1m_percent: Optional[float] = None
    change_ytd: Optional[float] = None
    change_ytd_percent: Optional[float] = None


class AllocationResponse(BaseModel):
    """Asset allocation response."""
    by_type: dict[str, float]
    by_currency: dict[str, float]
    by_country: dict[str, float]
    by_institution: dict[str, float]


class CurrencyExposureResponse(BaseModel):
    """Currency exposure response."""
    exposures: dict[str, float]  # Currency -> percentage
    amounts_usd: dict[str, float]  # Currency -> amount in USD
    risk_assessment: str  # "concentrated", "balanced", "diversified"


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
    currency_exposure: CurrencyExposureResponse
    growth: GrowthResponse


class FIREMetricsResponse(BaseModel):
    """FIRE calculation metrics response."""
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


class ProjectionPointResponse(BaseModel):
    """Single projection point."""
    year: int
    date: str
    net_worth: float
    contributions: float
    growth: float
    passive_income: float


class ScenarioResponse(BaseModel):
    """What-if scenario response."""
    name: str
    years_to_fire: Optional[float] = None
    fire_date: Optional[str] = None
    final_net_worth: float
    difference_years: Optional[float] = None


class FIRESummaryResponse(BaseModel):
    """Complete FIRE summary response."""
    metrics: FIREMetricsResponse
    projections: list[ProjectionPointResponse]
    scenarios: list[ScenarioResponse]


class FIRECalculationRequest(BaseModel):
    """Request body for custom FIRE calculations."""
    monthly_expenses: float = Field(default=5000, description="Monthly expenses in CAD")
    monthly_savings: float = Field(default=2000, description="Monthly savings in CAD")
    currency: str = Field(default="CAD", description="Currency of expenses/savings")
    safe_withdrawal_rate: float = Field(default=0.04, description="Safe withdrawal rate (e.g., 0.04 for 4%)")
    expected_return: float = Field(default=0.07, description="Expected annual return (e.g., 0.07 for 7%)")


class HistoricalDataPoint(BaseModel):
    """Historical data point for charting."""
    date: str
    net_worth: float
    cost_basis: Optional[float] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/summary", response_model=InsightsSummaryResponse)
def get_summary(
    base_currency: str = Query(default="USD", description="Base currency for calculations"),
    db: Session = Depends(get_db),
):
    """Get complete insights summary.
    
    Returns net worth, allocation, currency exposure, and growth metrics
    in a single call for dashboard efficiency.
    """
    summary = get_insights_summary(db, base_currency=base_currency)
    return InsightsSummaryResponse(
        net_worth=NetWorthResponse(**summary["net_worth"]),
        allocation=AllocationResponse(**summary["allocation"]),
        currency_exposure=CurrencyExposureResponse(**summary["currency_exposure"]),
        growth=GrowthResponse(**summary["growth"]),
    )


@router.get("/net-worth", response_model=NetWorthResponse)
def get_net_worth(
    base_currency: str = Query(default="USD", description="Base currency"),
    db: Session = Depends(get_db),
):
    """Get net worth summary."""
    calculator = InsightsCalculator(db, base_currency=base_currency)
    net_worth = calculator.calculate_net_worth()
    
    return NetWorthResponse(
        total_usd=float(net_worth.net_worth_usd),
        total_assets_usd=float(net_worth.total_assets_usd),
        total_liabilities_usd=float(net_worth.total_liabilities_usd),
        liquid_assets_usd=float(net_worth.liquid_assets_usd),
        investment_assets_usd=float(net_worth.investment_assets_usd),
        retirement_assets_usd=float(net_worth.retirement_assets_usd),
        real_estate_equity_usd=float(net_worth.real_estate_equity_usd),
        assets_by_currency={k: float(v) for k, v in net_worth.assets_by_currency.items()},
        liabilities_by_currency={k: float(v) for k, v in net_worth.liabilities_by_currency.items()},
        change_1d=float(net_worth.change_1d) if net_worth.change_1d else None,
        change_1d_percent=float(net_worth.change_1d_percent) if net_worth.change_1d_percent else None,
        change_1m=float(net_worth.change_1m) if net_worth.change_1m else None,
        change_1m_percent=float(net_worth.change_1m_percent) if net_worth.change_1m_percent else None,
        change_ytd=float(net_worth.change_ytd) if net_worth.change_ytd else None,
        change_ytd_percent=float(net_worth.change_ytd_percent) if net_worth.change_ytd_percent else None,
    )


@router.get("/allocation", response_model=AllocationResponse)
def get_allocation(db: Session = Depends(get_db)):
    """Get asset allocation breakdown."""
    calculator = InsightsCalculator(db)
    allocation = calculator.calculate_allocation()
    
    return AllocationResponse(
        by_type={k: float(v) for k, v in allocation.by_type.items()},
        by_currency={k: float(v) for k, v in allocation.by_currency.items()},
        by_country={k: float(v) for k, v in allocation.by_country.items()},
        by_institution={k: float(v) for k, v in allocation.by_institution.items()},
    )


@router.get("/currency-exposure", response_model=CurrencyExposureResponse)
def get_currency_exposure(db: Session = Depends(get_db)):
    """Get currency exposure analysis."""
    calculator = InsightsCalculator(db)
    exposure = calculator.calculate_currency_exposure()
    
    return CurrencyExposureResponse(
        exposures={k: float(v) for k, v in exposure.exposures.items()},
        amounts_usd={k: float(v) for k, v in exposure.amounts_usd.items()},
        risk_assessment=exposure.risk_assessment,
    )


@router.get("/growth", response_model=GrowthResponse)
def get_growth_metrics(db: Session = Depends(get_db)):
    """Get portfolio growth metrics."""
    calculator = InsightsCalculator(db)
    growth = calculator.calculate_growth_metrics()
    
    return GrowthResponse(
        monthly_rate=float(growth.monthly_growth_rate),
        yearly_rate=float(growth.yearly_growth_rate),
        average_monthly=float(growth.average_monthly_growth),
        best_month=growth.best_month.isoformat() if growth.best_month else None,
        best_month_return=float(growth.best_month_return) if growth.best_month_return else None,
        worst_month=growth.worst_month.isoformat() if growth.worst_month else None,
        worst_month_return=float(growth.worst_month_return) if growth.worst_month_return else None,
    )


@router.get("/historical", response_model=list[HistoricalDataPoint])
def get_historical_data(
    period: str = Query(default="1y", description="Period: 7d, 30d, 90d, 1y, all"),
    db: Session = Depends(get_db),
):
    """Get historical net worth data for charting."""
    calculator = InsightsCalculator(db)
    data = calculator.get_historical_net_worth(period=period)
    
    return [HistoricalDataPoint(**point) for point in data]


@router.get("/fire", response_model=FIRESummaryResponse)
def get_fire_metrics(
    monthly_expenses: float = Query(default=5000, description="Monthly expenses"),
    monthly_savings: float = Query(default=2000, description="Monthly savings"),
    currency: str = Query(default="CAD", description="Currency"),
    db: Session = Depends(get_db),
):
    """Get FIRE calculation summary.
    
    Returns FIRE metrics, 30-year projections, and what-if scenarios.
    """
    summary = get_fire_summary(
        db,
        monthly_expenses=Decimal(str(monthly_expenses)),
        monthly_savings=Decimal(str(monthly_savings)),
        currency=currency,
    )
    
    return FIRESummaryResponse(
        metrics=FIREMetricsResponse(**summary["metrics"]),
        projections=[ProjectionPointResponse(**p) for p in summary["projections"]],
        scenarios=[ScenarioResponse(**s) for s in summary["scenarios"]],
    )


@router.post("/fire/calculate", response_model=FIRESummaryResponse)
def calculate_fire(
    request: FIRECalculationRequest,
    db: Session = Depends(get_db),
):
    """Calculate FIRE metrics with custom parameters.
    
    Allows specifying custom SWR and expected return rates.
    """
    # Get current net worth
    calculator = InsightsCalculator(db)
    net_worth = calculator.calculate_net_worth()
    
    # Calculate FIRE
    fire_calc = FIRECalculator(db)
    metrics = fire_calc.calculate_fire_metrics(
        current_net_worth=net_worth.net_worth_usd,
        monthly_expenses=Decimal(str(request.monthly_expenses)),
        monthly_savings=Decimal(str(request.monthly_savings)),
        currency=request.currency,
        safe_withdrawal_rate=Decimal(str(request.safe_withdrawal_rate)),
        expected_return=Decimal(str(request.expected_return)),
    )
    
    # Get projections
    projections = fire_calc.project_net_worth(
        current_net_worth=net_worth.net_worth_usd,
        monthly_savings=fire_calc._convert_to_usd(
            Decimal(str(request.monthly_savings)), 
            request.currency
        ),
        years=30,
        annual_return=Decimal(str(request.expected_return)),
        safe_withdrawal_rate=Decimal(str(request.safe_withdrawal_rate)),
    )
    
    # Get scenarios
    scenarios = fire_calc.run_what_if_scenarios(
        current_net_worth=net_worth.net_worth_usd,
        monthly_expenses=Decimal(str(request.monthly_expenses)),
        monthly_savings=Decimal(str(request.monthly_savings)),
        currency=request.currency,
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
    current_net_worth: Optional[float] = Query(default=None, description="Override current net worth"),
    monthly_savings: float = Query(default=2000, description="Monthly savings"),
    years: int = Query(default=30, description="Years to project"),
    annual_return: float = Query(default=0.07, description="Expected annual return"),
    currency: str = Query(default="CAD", description="Currency of savings"),
    db: Session = Depends(get_db),
):
    """Get net worth projections over time."""
    # Get current net worth if not provided
    if current_net_worth is None:
        calculator = InsightsCalculator(db)
        net_worth = calculator.calculate_net_worth()
        current_net_worth = float(net_worth.net_worth_usd)
    
    fire_calc = FIRECalculator(db)
    monthly_savings_usd = float(fire_calc._convert_to_usd(
        Decimal(str(monthly_savings)), 
        currency
    ))
    
    projections = fire_calc.project_net_worth(
        current_net_worth=Decimal(str(current_net_worth)),
        monthly_savings=Decimal(str(monthly_savings_usd)),
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
