"""Decimal money totals, per currency first, with explicit FX provenance.

Rules:

* Aggregate in ``Decimal`` and quantize to two places (ROUND_HALF_UP) at the
  reporting boundary, never in between.
* Totals are kept **per original currency**. Converting to a reporting
  currency is a separate, explicit step that records which rate was used.
* A missing rate is never papered over with a fallback. The amount stays in
  ``unconverted`` and ``fx_complete`` is ``False``.
* These reporting conversions are for Wallet display and analysis. They are
  not tax conversion rates.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from backend.services import fx

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")
CONVERTIBLE = frozenset({"CAD", "USD"})


def quantize(value: Decimal | int | float | str) -> Decimal:
    """Round to cents with ROUND_HALF_UP."""
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass
class CurrencyFlow:
    """Income and expense totals in one currency."""

    income: Decimal = ZERO
    expenses: Decimal = ZERO

    @property
    def net(self) -> Decimal:
        return self.income - self.expenses

    def add(self, kind: str, amount: Decimal) -> None:
        if kind == "income":
            self.income += amount
        elif kind == "expense":
            self.expenses += amount
        else:
            raise ValueError(f"Unknown flow kind {kind!r}")

    def quantized(self) -> CurrencyFlow:
        return CurrencyFlow(quantize(self.income), quantize(self.expenses))


@dataclass(frozen=True)
class FxQuote:
    """A rate observation: ``rate`` is "1 unit of base in quote" (USDCAD = 1 USD in CAD)."""

    pair: str
    rate: Decimal
    as_of: date
    source: str | None = None


@dataclass(frozen=True)
class FxProvenance:
    """Which quote converted which currency, recorded on every converted total."""

    from_currency: str
    to_currency: str
    pair: str
    rate: Decimal
    as_of: date
    source: str | None = None


RateLookup = Callable[[date], FxQuote | None]
"""Return the USD/CAD quote in effect on or before a date, or ``None``."""


@dataclass
class ReportingTotals:
    """Totals expressed in one reporting currency, plus what could not be converted."""

    currency: str
    income: Decimal = ZERO
    expenses: Decimal = ZERO
    fx_complete: bool = True
    unconverted: dict[str, CurrencyFlow] = field(default_factory=dict)
    fx: list[FxProvenance] = field(default_factory=list)

    @property
    def net(self) -> Decimal:
        return self.income - self.expenses


def savings_rate(totals: CurrencyFlow | ReportingTotals) -> float | None:
    """``net / income`` as a ratio, or ``None`` when there is no income."""
    if totals.income <= 0:
        return None
    return float(totals.net / totals.income)


def to_reporting(
    by_currency: Mapping[str, CurrencyFlow],
    reporting: str,
    rate_on: RateLookup,
    as_of: date,
) -> ReportingTotals:
    """Express per-currency flows in ``reporting`` using the quote for ``as_of``.

    Same-currency flows pass through. CAD<->USD flows convert with the quote
    returned by ``rate_on(as_of)``. Anything else, or any flow for which no
    quote exists, is left in ``unconverted`` and marks the result incomplete.
    """
    reporting = reporting.upper()
    if reporting not in CONVERTIBLE:
        raise ValueError(f"reporting currency must be CAD or USD, got {reporting!r}")

    result = ReportingTotals(currency=reporting)
    quote: FxQuote | None = None
    quote_resolved = False

    for raw_currency, flow in by_currency.items():
        currency = (raw_currency or "").upper()
        if currency == reporting:
            result.income += flow.income
            result.expenses += flow.expenses
            continue
        if currency not in CONVERTIBLE:
            result.unconverted[currency] = flow.quantized()
            result.fx_complete = False
            continue
        if not quote_resolved:
            quote = rate_on(as_of)
            quote_resolved = True
        if quote is None:
            result.unconverted[currency] = flow.quantized()
            result.fx_complete = False
            continue
        result.income += fx.convert(flow.income, from_ccy=currency, to_ccy=reporting, usd_cad_rate=quote.rate)
        result.expenses += fx.convert(flow.expenses, from_ccy=currency, to_ccy=reporting, usd_cad_rate=quote.rate)
        result.fx.append(
            FxProvenance(
                from_currency=currency,
                to_currency=reporting,
                pair=quote.pair,
                rate=quote.rate,
                as_of=quote.as_of,
                source=quote.source,
            )
        )

    result.income = quantize(result.income)
    result.expenses = quantize(result.expenses)
    return result
