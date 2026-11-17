"""Per-currency totals and explicit FX in the calculation contract."""

from datetime import date
from decimal import Decimal

import pytest

from backend.services.calculation import CurrencyFlow, FxQuote, quantize, savings_rate, to_reporting

AS_OF = date(2026, 3, 31)
USDCAD = FxQuote(pair="USDCAD", rate=Decimal("1.35000000"), as_of=date(2026, 3, 30), source="bank_of_canada")


def no_rate(_: date) -> FxQuote | None:
    return None


def fixed_rate(_: date) -> FxQuote | None:
    return USDCAD


def test_quantize_rounds_half_up_to_cents():
    assert quantize("10.005") == Decimal("10.01")
    assert quantize(Decimal("0.1") + Decimal("0.2")) == Decimal("0.30")


def test_currency_flow_net_and_savings_rate():
    flow = CurrencyFlow(income=Decimal("5000.00"), expenses=Decimal("3500.00"))
    assert flow.net == Decimal("1500.00")
    assert savings_rate(flow) == pytest.approx(0.3)
    assert savings_rate(CurrencyFlow()) is None


def test_cad_only_is_complete_without_touching_fx():
    def exploding_lookup(_: date) -> FxQuote | None:
        raise AssertionError("rate lookup must not run for same-currency totals")

    totals = to_reporting({"CAD": CurrencyFlow(Decimal("100.10"), Decimal("40.05"))}, "CAD", exploding_lookup, AS_OF)

    assert totals.income == Decimal("100.10")
    assert totals.expenses == Decimal("40.05")
    assert totals.net == Decimal("60.05")
    assert totals.fx_complete is True
    assert totals.unconverted == {}
    assert totals.fx == []


def test_usd_converts_with_recorded_provenance():
    flows = {
        "CAD": CurrencyFlow(Decimal("1000.00"), Decimal("200.00")),
        "USD": CurrencyFlow(Decimal("100.00"), Decimal("10.00")),
    }
    totals = to_reporting(flows, "CAD", fixed_rate, AS_OF)

    assert totals.income == Decimal("1135.00")
    assert totals.expenses == Decimal("213.50")
    assert totals.fx_complete is True
    assert len(totals.fx) == 1
    provenance = totals.fx[0]
    assert (provenance.from_currency, provenance.to_currency) == ("USD", "CAD")
    assert provenance.rate == Decimal("1.35000000")
    assert provenance.as_of == date(2026, 3, 30)  # the observation date, not the requested one
    assert provenance.source == "bank_of_canada"


def test_reporting_in_usd_divides_cad():
    totals = to_reporting({"CAD": CurrencyFlow(Decimal("135.00"), Decimal("0"))}, "USD", fixed_rate, AS_OF)
    assert totals.income == Decimal("100.00")


def test_missing_rate_is_explicit_not_guessed():
    flows = {
        "CAD": CurrencyFlow(Decimal("1000.00"), Decimal("200.00")),
        "USD": CurrencyFlow(Decimal("100.00"), Decimal("10.00")),
    }
    totals = to_reporting(flows, "CAD", no_rate, AS_OF)

    assert totals.income == Decimal("1000.00")  # USD not folded in
    assert totals.fx_complete is False
    assert totals.unconverted == {"USD": CurrencyFlow(Decimal("100.00"), Decimal("10.00"))}
    assert totals.fx == []


def test_unsupported_currency_is_left_unconverted_even_with_a_rate():
    totals = to_reporting({"EUR": CurrencyFlow(Decimal("5.00"), Decimal("0"))}, "CAD", fixed_rate, AS_OF)
    assert totals.fx_complete is False
    assert "EUR" in totals.unconverted
    assert totals.income == Decimal("0.00")


def test_reporting_currency_must_be_cad_or_usd():
    with pytest.raises(ValueError):
        to_reporting({}, "EUR", fixed_rate, AS_OF)
