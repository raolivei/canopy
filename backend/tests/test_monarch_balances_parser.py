"""Tests for the Monarch balances CSV parser."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.services.monarch.balances_parser import (
    looks_like_balances_header,
    parse_monarch_balances_csv,
)
from backend.services.monarch.parser import AccountClass

HEADER = "Date,Balance,Account\n"


def _body(*rows: str) -> str:
    return HEADER + "\n".join(rows) + "\n"


def test_header_detection_matches_only_balances_shape() -> None:
    assert looks_like_balances_header("Date,Balance,Account")
    assert looks_like_balances_header("Date,Balance,Account,extra")  # tolerant
    assert not looks_like_balances_header(
        "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags"
    )
    assert not looks_like_balances_header("")


def test_parses_asset_cash_liability_and_investment_rows() -> None:
    csv = _body(
        "2026-03-25,9677.84,RBC Day to Day Banking (...8813)",
        "2026-03-25,-21818.66,RBC Visa Classic Low Rate Option (...7192)",
        "2026-03-25,132608.79,MANAGED_RRSP (...z4qw)",
    )
    result = parse_monarch_balances_csv(csv)
    assert result.header_ok
    assert len(result.rows) == 3

    by_label = {r.account_label: r for r in result.rows}
    rbc = by_label["RBC Day to Day Banking (...8813)"]
    assert rbc.account_class == AccountClass.CASH
    assert rbc.balance == Decimal("9677.84")
    assert rbc.currency == "CAD"
    assert rbc.as_of == date(2026, 3, 25)
    assert rbc.account_last4 == "8813"

    visa = by_label["RBC Visa Classic Low Rate Option (...7192)"]
    assert visa.account_class == AccountClass.DEBT
    assert visa.balance == Decimal("-21818.66")

    rrsp = by_label["MANAGED_RRSP (...z4qw)"]
    assert rrsp.account_class == AccountClass.INVESTMENT
    assert rrsp.currency == "CAD"


def test_skips_pseudo_and_foreign_currency_accounts() -> None:
    csv = _body(
        "2026-03-25,123.45,CAD account (...1618)",
        "2026-03-25,987.00,EUR account (...0991)",
        "2026-03-25,10000.00,TRY account (...3253)",
        "2026-03-25,0.00,Transfer",
    )
    result = parse_monarch_balances_csv(csv)
    assert result.header_ok
    assert len(result.rows) == 1  # only the CAD account survives
    assert result.skipped_foreign == 2
    assert result.skipped_pseudo == 1


def test_infers_usd_currency_from_label_prefix() -> None:
    csv = _body(
        "2026-03-25,501.23,USD account (...2015)",
    )
    result = parse_monarch_balances_csv(csv)
    assert result.header_ok
    assert len(result.rows) == 1
    assert result.rows[0].currency == "USD"


def test_header_mismatch_produces_no_rows_and_sets_flag_false() -> None:
    bad = "Day,Saldo,Conta\n2026-03-25,100.00,Foo\n"
    result = parse_monarch_balances_csv(bad)
    assert not result.header_ok
    assert result.rows == []
    assert any("missing required column" in w for w in result.warnings)


def test_malformed_row_is_skipped_with_warning() -> None:
    csv = _body(
        "not-a-date,100.00,RBC Day to Day Banking (...8813)",
        "2026-03-25,,RBC Day to Day Banking (...8813)",
        "2026-03-25,abc,RBC Day to Day Banking (...8813)",
        "2026-03-25,50.00,RBC Day to Day Banking (...8813)",
    )
    result = parse_monarch_balances_csv(csv)
    assert result.header_ok
    assert len(result.rows) == 1
    assert result.rows[0].balance == Decimal("50.00")
    assert len(result.warnings) >= 3
