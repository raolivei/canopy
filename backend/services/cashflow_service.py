"""Cash-flow analytics built on the shared calculation contract.

Every figure here comes from ``backend.services.calculation``: calendar
months, flow classification by type, per-currency Decimal totals, explicit
FX with provenance. Nothing in this module approximates a month or sums
currencies together.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Literal

from backend.services.calculation import (
    ZERO,
    CurrencyFlow,
    FlowKind,
    FlowRow,
    PeriodKind,
    bucket_by_category,
    bucket_by_month,
    month_bounds,
    month_key,
    monthly_flows,
    months_back,
    months_between,
    parse_month,
    period_bounds,
    prior_period_bounds,
    quantize,
    rate_lookup,
    savings_rate,
    to_reporting,
    zero_fill,
)
from sqlalchemy.orm import Session

ReportingCurrency = Literal["CAD", "USD"]
Trend = Literal["improving", "declining", "stable", "no_data"]
Volatility = Literal["low", "moderate", "high", "no_data"]


def _flow_dict(flow: CurrencyFlow) -> dict[str, Decimal]:
    q = flow.quantized()
    return {"income": q.income, "expenses": q.expenses, "net": q.net}


def _merge_flows(buckets: list[dict[str, CurrencyFlow]]) -> dict[str, CurrencyFlow]:
    merged: dict[str, CurrencyFlow] = {}
    for flows in buckets:
        for currency, flow in flows.items():
            target = merged.setdefault(currency, CurrencyFlow())
            target.income += flow.income
            target.expenses += flow.expenses
    return merged


class CashflowService:
    """Monthly cash-flow metrics in a reporting currency with explicit FX."""

    def __init__(self, db: Session, reporting_currency: str = "CAD"):
        self.db = db
        self.reporting_currency = reporting_currency.upper()
        self._rate_on = rate_lookup(db)

    # ------------------------------------------------------------------ helpers

    def _report(self, flows: dict[str, CurrencyFlow], as_of: date) -> dict[str, Any]:
        """Reporting-currency view of per-currency flows, with provenance."""
        totals = to_reporting(flows, self.reporting_currency, self._rate_on, as_of)
        return {
            "currency": totals.currency,
            "income": totals.income,
            "expenses": totals.expenses,
            "net": totals.net,
            "savings_rate": savings_rate(totals),
            "by_currency": {ccy: _flow_dict(flow) for ccy, flow in sorted(flows.items())},
            "fx_complete": totals.fx_complete,
            "unconverted": {ccy: _flow_dict(flow) for ccy, flow in sorted(totals.unconverted.items())},
            "fx": [asdict(p) for p in totals.fx],
        }

    @staticmethod
    def _month_end(year: int, month: int) -> date:
        return month_bounds(year, month)[1] - timedelta(days=1)

    # ------------------------------------------------------------------ queries

    def get_monthly_summary(self, start: date, end: date) -> list[dict[str, Any]]:
        """Income, expenses and net per calendar month for ``start``..``end`` inclusive.

        Months without transactions are present with zero totals.
        """
        if start > end:
            raise ValueError("start must be on or before end")
        months = months_between(start, end)
        rows = monthly_flows(self.db, start, end + timedelta(days=1))
        buckets = zero_fill(bucket_by_month(rows), months)
        return [
            {
                "month": month_key(year, month),
                **self._report(buckets[month_key(year, month)], self._month_end(year, month)),
            }
            for year, month in months
        ]

    def get_cashflow_trend(self, months: int = 12, *, today: date | None = None) -> dict[str, Any]:
        """Last ``months`` calendar months (including the current one) with averages and a trend label."""
        today = today or date.today()
        window = months_back(today, months)
        start = month_bounds(*window[0])[0]
        end_exclusive = month_bounds(*window[-1])[1]
        rows = monthly_flows(self.db, start, end_exclusive)
        buckets = zero_fill(bucket_by_month(rows), window)
        monthly = [
            {
                "month": month_key(year, month),
                **self._report(buckets[month_key(year, month)], self._month_end(year, month)),
            }
            for year, month in window
        ]

        count = Decimal(len(monthly))
        avg_income = quantize(sum((m["income"] for m in monthly), ZERO) / count)
        avg_expenses = quantize(sum((m["expenses"] for m in monthly), ZERO) / count)
        avg_net = quantize(sum((m["net"] for m in monthly), ZERO) / count)

        trend: Trend = "stable"
        if not rows:
            trend = "no_data"
        elif len(monthly) >= 6:
            recent = sum((m["net"] for m in monthly[-3:]), ZERO) / 3
            previous = sum((m["net"] for m in monthly[-6:-3]), ZERO) / 3
            if recent > previous * Decimal("1.1"):
                trend = "improving"
            elif recent < previous * Decimal("0.9"):
                trend = "declining"

        return {
            "months": months,
            "monthly_data": monthly,
            "average_income": avg_income,
            "average_expenses": avg_expenses,
            "average_net": avg_net,
            "trend": trend,
            "currency": self.reporting_currency,
            "fx_complete": all(m["fx_complete"] for m in monthly),
        }

    def get_category_breakdown(
        self,
        month: str | None = None,
        *,
        kind: FlowKind = "expense",
        today: date | None = None,
    ) -> dict[str, Any]:
        """Totals per category for one calendar month, for ``kind`` flows only."""
        today = today or date.today()
        year, month_num = parse_month(month) if month else (today.year, today.month)
        start, end_exclusive = month_bounds(year, month_num)
        as_of = end_exclusive - timedelta(days=1)

        rows = [r for r in monthly_flows(self.db, start, end_exclusive, by_category=True) if r.kind == kind]
        by_category = bucket_by_category(rows)
        field = "income" if kind == "income" else "expenses"

        items: list[dict[str, Any]] = []
        for category, flows in by_category.items():
            report = self._report(flows, as_of)
            items.append(
                {
                    "category": category,
                    "amount": report[field],
                    "by_currency": report["by_currency"],
                    "fx_complete": report["fx_complete"],
                    "unconverted": report["unconverted"],
                }
            )
        total_report = self._report(_merge_flows(list(by_category.values())), as_of)
        total = total_report[field]
        for item in items:
            item["percentage"] = float(item["amount"] / total * 100) if total > 0 else 0.0
        items.sort(key=lambda item: (-item["amount"], item["category"]))

        return {
            "month": month_key(year, month_num),
            "kind": kind,
            "total": total,
            "categories": items,
            "currency": self.reporting_currency,
            "fx_complete": total_report["fx_complete"],
            "unconverted": total_report["unconverted"],
            "fx": total_report["fx"],
        }

    def calculate_burn_rate(self, months: int = 3, *, today: date | None = None) -> dict[str, Any]:
        """Average monthly spending over the months in the window that have expenses."""
        today = today or date.today()
        window = months_back(today, months)
        start = month_bounds(*window[0])[0]
        end_exclusive = month_bounds(*window[-1])[1]
        rows = [r for r in monthly_flows(self.db, start, end_exclusive) if r.kind == "expense"]
        buckets = bucket_by_month(rows)

        breakdown: list[dict[str, Any]] = []
        fx_complete = True
        for key in sorted(buckets):
            year, month_num = parse_month(key)
            report = self._report(buckets[key], self._month_end(year, month_num))
            breakdown.append({"month": key, "amount": report["expenses"]})
            fx_complete = fx_complete and report["fx_complete"]

        if not breakdown:
            return {
                "months_analyzed": 0,
                "average_monthly_burn": ZERO,
                "monthly_breakdown": [],
                "min_month": None,
                "max_month": None,
                "volatility": "no_data",
                "currency": self.reporting_currency,
                "fx_complete": True,
            }

        amounts = [b["amount"] for b in breakdown]
        average = quantize(sum(amounts, ZERO) / Decimal(len(amounts)))
        min_month = min(breakdown, key=lambda b: (b["amount"], b["month"]))
        max_month = max(breakdown, key=lambda b: (b["amount"], b["month"]))

        volatility: Volatility = "no_data"
        if average > 0:
            mean = float(average)
            variance = sum((float(a) - mean) ** 2 for a in amounts) / len(amounts)
            coefficient = (variance**0.5) / mean * 100
            volatility = "low" if coefficient < 10 else "moderate" if coefficient < 20 else "high"

        return {
            "months_analyzed": len(breakdown),
            "average_monthly_burn": average,
            "monthly_breakdown": breakdown,
            "min_month": min_month,
            "max_month": max_month,
            "volatility": volatility,
            "currency": self.reporting_currency,
            "fx_complete": fx_complete,
        }

    def get_comparison(
        self,
        kind: PeriodKind = "month",
        reference: str | None = None,
        *,
        today: date | None = None,
    ) -> dict[str, Any]:
        """Current period versus the immediately preceding period of the same kind.

        ``reference`` is ``YYYY-MM``; the period of ``kind`` containing that
        month is "current". Defaults to the period containing today.
        """
        today = today or date.today()
        year, month_num = parse_month(reference) if reference else (today.year, today.month)
        current_start, current_end = period_bounds(kind, year, month_num)
        prior_start, prior_end = prior_period_bounds(kind, current_start)
        rows = monthly_flows(self.db, prior_start, current_end)

        def totals(start: date, end_exclusive: date) -> dict[str, Any]:
            in_period = [r for r in rows if start <= date(r.year, r.month, 1) < end_exclusive]
            flows = _merge_flows(list(bucket_by_month(in_period).values()))
            as_of = end_exclusive - timedelta(days=1)
            return {"start": start, "end": as_of, **self._report(flows, as_of)}

        current = totals(current_start, current_end)
        prior = totals(prior_start, prior_end)
        delta = {
            "income": current["income"] - prior["income"],
            "expenses": current["expenses"] - prior["expenses"],
            "net": current["net"] - prior["net"],
            "savings_rate_points": (
                (current["savings_rate"] - prior["savings_rate"]) * 100
                if current["savings_rate"] is not None and prior["savings_rate"] is not None
                else None
            ),
        }
        return {
            "kind": kind,
            "current": current,
            "prior": prior,
            "delta": delta,
            "currency": self.reporting_currency,
            "fx_complete": current["fx_complete"] and prior["fx_complete"],
        }


__all__ = ["CashflowService", "FlowRow", "ReportingCurrency"]
