"""Tests for the Wealthsimple description micro-parser."""

from __future__ import annotations

from decimal import Decimal

from backend.services.wealthsimple.description_parser import (
    parse_buy,
    parse_direct_deposit,
    parse_div,
    parse_sell,
    parse_share_transfer,
)


def test_parse_buy_with_fx_rate() -> None:
    desc = "CRM - Salesforce Inc.: Bought 0.0371 shares at $192.11 per share (executed at 2026-03-03), FX Rate: 1.3679"
    info = parse_buy(desc)
    assert info is not None
    assert info.ticker == "CRM"
    assert info.name == "Salesforce Inc."
    assert info.shares == Decimal("0.0371")
    assert info.price == Decimal("192.11")
    assert info.executed_at.isoformat() == "2026-03-03"
    assert info.fx_rate == Decimal("1.3679")


def test_parse_buy_without_fx() -> None:
    desc = "MSFT - Microsoft CDR (CAD Hedged): Bought 30.0000 shares at $27.78 per share (executed at 2026-03-02)"
    info = parse_buy(desc)
    assert info is not None
    assert info.ticker == "MSFT"
    assert info.fx_rate is None


def test_parse_sell_with_backtick_name() -> None:
    desc = "LOW - Lowe`s Cos., Inc.: Sold 0.0073 shares at $253.47 per share (executed at 2026-03-03), FX Rate: 1.3679"
    info = parse_sell(desc)
    assert info is not None
    assert info.ticker == "LOW"
    assert "Lowe" in info.name
    assert info.shares == Decimal("0.0073")


def test_parse_dividend_with_fx() -> None:
    desc = (
        "WEC - WEC Energy Group Inc: Cash dividend distribution, received on "
        "2026-03-02, record date of 2026-02-13, FX Rate: 1.3757"
    )
    info = parse_div(desc)
    assert info is not None
    assert info.ticker == "WEC"
    assert info.pay_date.isoformat() == "2026-03-02"
    assert info.record_date.isoformat() == "2026-02-13"
    assert info.fx_rate == Decimal("1.3757")


def test_parse_dividend_without_fx() -> None:
    desc = (
        "ZUAG.F - BMO US Aggregate Bond Index ETF Hedged: Cash dividend "
        "distribution, received on 2026-03-03, record date of 2026-02-26"
    )
    info = parse_div(desc)
    assert info is not None
    assert info.ticker == "ZUAG.F"
    assert info.fx_rate is None


def test_parse_share_transfer_out() -> None:
    desc = (
        "SKYY - First Trust Cloud Computing ETF: Tax-free transfer of "
        "10.0000 shares out of the account (executed at 2026-03-06)"
    )
    info = parse_share_transfer(desc)
    assert info is not None
    assert info.ticker == "SKYY"
    assert info.shares == Decimal("10.0000")


def test_parse_direct_deposit() -> None:
    desc = "Direct deposit from MOMENTIVE CANAD"
    info = parse_direct_deposit(desc)
    assert info is not None
    assert info.employer == "MOMENTIVE CANAD"


def test_parse_buy_rejects_unrelated_text() -> None:
    assert parse_buy("Tax-free money transfer out of the account") is None
    assert parse_sell("Interest earned") is None
    assert parse_div("Management fees for period 2026-03-01 to 2026-03-31") is None
