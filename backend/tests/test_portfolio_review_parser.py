"""Tests for portfolio review CSV/TSV parser."""

from decimal import Decimal
from pathlib import Path

import pytest

from backend.services.portfolio_review_parser import (
    parse_portfolio_review_text,
    total_usd,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "portfolio_review_sample.csv"


def test_parser_reads_sample_fixture() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    assert parsed.as_of_date.isoformat() == "2026-04-15"
    assert len(parsed.lines) == 3


def test_brazil_fii_row_present() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    br = [ln for ln in parsed.lines if ln.region == "BR"]
    assert len(br) == 1
    assert "CPTS11" in br[0].investment
    assert br[0].value_native == Decimal("10000")
    assert br[0].value_usd == Decimal("2000")


def test_plan_row_with_em_dash_skipped() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    qt = [ln for ln in parsed.lines if "VTI (QT)" in ln.investment]
    assert not qt


def test_crypto_div_strips_footnote() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    cr = [ln for ln in parsed.lines if ln.region == "CRYPTO"][0]
    assert cr.div_per_year == Decimal("320")


def test_total_usd_sums_lines() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    assert total_usd(parsed.lines) == Decimal("2000") + Decimal("3500") + Decimal("6000")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1,234.56", Decimal("1234.56")),
        ("~10%", Decimal("10")),
        ("—", None),
    ],
)
def test_parse_decimal_helpers(raw: str, expected: Decimal | None) -> None:
    from backend.services.portfolio_review_parser import _parse_decimal

    assert _parse_decimal(raw) == expected


def test_tab_delimited_section_still_parses() -> None:
    """TSV rows remain supported alongside comma exports."""
    text = """🇧🇷 Brazil Portfolio
15 Apr 2026
Investment\tPlatform\tCurrency\tValue (BRL)\tUSD\t% Brazil\t% Global\tReturn\tDiv/Yr\tYield\tFX\tTarget %\tDelta\tConviction\tAction
ZZ11\tXP\tBRL\t100\t50\t1\t1\t—\t—\t—\tBRL\t—\t—\t1\tHold
"""
    parsed = parse_portfolio_review_text(text)
    assert len(parsed.lines) == 1
    assert parsed.lines[0].investment == "ZZ11"
    assert parsed.lines[0].value_usd == Decimal("50")
