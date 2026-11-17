"""Shared calculation contract.

One place for the rules every money figure in Canopy must follow: calendar
periods, flow classification, per-currency Decimal totals with explicit FX
provenance, and SQL-side aggregation. Pages, exports and assistant tools all
build on this package so the same period and filters give the same numbers.

See docs/CALCULATION_CONTRACT.md for the written contract.
"""

from backend.services.calculation.aggregate import (
    FlowRow,
    bucket_by_category,
    bucket_by_month,
    monthly_flows,
    rate_lookup,
    zero_fill,
)
from backend.services.calculation.flows import (
    EXCLUDED_TYPES,
    EXPENSE_TYPES,
    FLOW_TYPES,
    INCOME_TYPES,
    FlowKind,
    classify,
)
from backend.services.calculation.money import (
    ZERO,
    CurrencyFlow,
    FxProvenance,
    FxQuote,
    RateLookup,
    ReportingTotals,
    quantize,
    savings_rate,
    to_reporting,
)
from backend.services.calculation.periods import (
    PeriodKind,
    add_months,
    as_datetime_range,
    month_bounds,
    month_key,
    months_back,
    months_between,
    parse_month,
    period_bounds,
    prior_period_bounds,
    quarter_bounds,
    year_bounds,
)

__all__ = [
    "EXCLUDED_TYPES",
    "EXPENSE_TYPES",
    "FLOW_TYPES",
    "INCOME_TYPES",
    "ZERO",
    "CurrencyFlow",
    "FlowKind",
    "FlowRow",
    "FxProvenance",
    "FxQuote",
    "PeriodKind",
    "RateLookup",
    "ReportingTotals",
    "add_months",
    "as_datetime_range",
    "bucket_by_category",
    "bucket_by_month",
    "classify",
    "month_bounds",
    "month_key",
    "monthly_flows",
    "months_back",
    "months_between",
    "parse_month",
    "period_bounds",
    "prior_period_bounds",
    "quantize",
    "quarter_bounds",
    "rate_lookup",
    "savings_rate",
    "to_reporting",
    "year_bounds",
    "zero_fill",
]
