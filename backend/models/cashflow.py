"""Pydantic schemas for the cash-flow API.

Money fields are ``Decimal`` in Python and 2-decimal JSON numbers on the
wire (see ``backend.models.money``). Every total carries its reporting
currency, the per-currency breakdown it was built from, and FX provenance.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from backend.models.money import Money, Rate

FlowKind = Literal["income", "expense"]
PeriodKind = Literal["month", "quarter", "year"]
ReportingCurrency = Literal["CAD", "USD"]


class CurrencyFlowOut(BaseModel):
    """Totals in one original currency."""

    income: Money
    expenses: Money
    net: Money


class FxProvenanceOut(BaseModel):
    """Which rate converted which currency into the reporting currency."""

    from_currency: str
    to_currency: str
    pair: str
    rate: Rate
    as_of: date = Field(description="Observation date of the rate actually used")
    source: str | None = None


class ReportingTotalsOut(BaseModel):
    """Reporting-currency totals plus what they were built from."""

    currency: str
    income: Money
    expenses: Money
    net: Money
    savings_rate: float | None = Field(None, description="net / income, or null without income")
    by_currency: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    fx_complete: bool = Field(description="False when some currency could not be converted")
    unconverted: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    fx: list[FxProvenanceOut] = Field(default_factory=list)


class MonthlySummary(ReportingTotalsOut):
    month: str = Field(description="YYYY-MM")


class MonthlySummaryResponse(BaseModel):
    data: list[MonthlySummary]
    total_months: int
    currency: str
    fx_complete: bool


class CashflowTrendResponse(BaseModel):
    months: int
    monthly_data: list[MonthlySummary]
    average_income: Money
    average_expenses: Money
    average_net: Money
    trend: Literal["improving", "declining", "stable", "no_data"]
    currency: str
    fx_complete: bool


class CategoryBreakdownItem(BaseModel):
    category: str
    amount: Money
    percentage: float = Field(ge=0, le=100)
    by_currency: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    fx_complete: bool
    unconverted: dict[str, CurrencyFlowOut] = Field(default_factory=dict)


class CategoryBreakdownResponse(BaseModel):
    month: str
    kind: FlowKind
    total: Money
    categories: list[CategoryBreakdownItem]
    currency: str
    fx_complete: bool
    unconverted: dict[str, CurrencyFlowOut] = Field(default_factory=dict)
    fx: list[FxProvenanceOut] = Field(default_factory=list)


class MonthlyBurn(BaseModel):
    month: str
    amount: Money


class BurnRateResponse(BaseModel):
    months_analyzed: int = Field(description="Months in the window that had expenses")
    average_monthly_burn: Money
    monthly_breakdown: list[MonthlyBurn]
    min_month: MonthlyBurn | None
    max_month: MonthlyBurn | None
    volatility: Literal["low", "moderate", "high", "no_data"]
    currency: str
    fx_complete: bool


class PeriodTotals(ReportingTotalsOut):
    start: date
    end: date = Field(description="Last day of the period (inclusive)")


class ComparisonDelta(BaseModel):
    income: Money
    expenses: Money
    net: Money
    savings_rate_points: float | None


class ComparisonResponse(BaseModel):
    kind: PeriodKind
    current: PeriodTotals
    prior: PeriodTotals
    delta: ComparisonDelta
    currency: str
    fx_complete: bool
