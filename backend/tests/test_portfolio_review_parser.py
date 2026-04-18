"""Tests for the Canadian (CAD-only) portfolio review CSV/TSV parser."""

from decimal import Decimal
from pathlib import Path

import pytest

from backend.services.portfolio_review_parser import (
    parse_portfolio_review_text,
    total_cad,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "portfolio_review_sample.csv"


def test_parser_reads_sample_fixture() -> None:
    """Only the Canada section contributes lines; Brazil/Crypto are skipped."""
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    assert parsed.as_of_date.isoformat() == "2026-04-15"
    assert len(parsed.lines) == 1
    assert parsed.lines[0].investment == "VCN"
    assert parsed.lines[0].platform == "Vanguard"
    assert parsed.lines[0].value_cad == Decimal("5000")


def test_brazil_and_crypto_sections_ignored() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    investments = {ln.investment for ln in parsed.lines}
    assert "CPTS11" not in investments  # Brazil row dropped
    assert "BTC" not in investments  # Crypto row dropped


def test_plan_row_with_em_dash_skipped() -> None:
    """Canada section rows with no CAD value (planned buys) are skipped."""
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    assert not [ln for ln in parsed.lines if "VTI (QT)" in ln.investment]


def test_total_cad_sums_lines() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    parsed = parse_portfolio_review_text(text)
    assert total_cad(parsed.lines) == Decimal("5000")


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


def test_tab_delimited_canada_section_parses() -> None:
    """TSV rows in the Canada section remain supported alongside comma exports."""
    text = (
        "🇨🇦 Canada Portfolio\n"
        "15 Apr 2026\n"
        "Investment\tPlatform\tValue (CAD)\t% Global\tReturn\tDiv/Yr\tYield\tTarget %\tDelta\tConviction\tAction\n"
        "VCN\tVanguard\t5000\t5\t—\t—\t—\t—\t—\t3\tHold\n"
    )
    parsed = parse_portfolio_review_text(text)
    assert len(parsed.lines) == 1
    assert parsed.lines[0].investment == "VCN"
    assert parsed.lines[0].value_cad == Decimal("5000")
    assert parsed.lines[0].pct_global == Decimal("5")


def test_legacy_multiregion_csv_only_keeps_canada() -> None:
    """A CSV with Brazil + Canada + Crypto sections keeps only the Canada rows."""
    text = (
        "🇧🇷 Brazil Portfolio\n"
        "15 Apr 2026\n"
        "Investment,Platform,Currency,Value (BRL),USD,% Brazil,% Global,Return,Div/Yr,Yield,FX,Target %,Delta,Conviction,Action\n"
        "CPTS11,FII XP,BRL,\"10,000\",\"2,000\",1.5%,0.5%,—,—,—,BRL,—,—,4,Hold\n"
        "🇨🇦 Canada Portfolio\n"
        "Investment,Platform,Value (CAD),% Global,Return,Div/Yr,Yield,Target %,Delta,Conviction,Action\n"
        "VCN,Vanguard,\"5,000\",5,—,—,—,—,—,3,Hold\n"
        "VFV,Vanguard,\"3,500\",3,—,—,—,—,—,4,Hold\n"
        "₿ CRYPTO Portfolio\n"
        "Investment,Platform,Currency,Value (CAD),USD,% Crypto,% Global,Return,Div/Yr,Yield,FX,Target %,Delta,Conviction,Action\n"
        "BTC,NDAX,CAD,\"8,000\",\"6,000\",2%,1%,—,—,—,USD,—,—,5,Hold\n"
    )
    parsed = parse_portfolio_review_text(text)
    investments = [ln.investment for ln in parsed.lines]
    assert investments == ["VCN", "VFV"]
    assert total_cad(parsed.lines) == Decimal("8500")
