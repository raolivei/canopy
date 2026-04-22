"""Tests for the Monarch CSV parser.

Covers header detection, account classification (investment / cash /
debt / foreign / pseudo), currency inference, last-4 extraction, and
the pseudo-account skip list.
"""

from __future__ import annotations

from decimal import Decimal

from backend.services.monarch.parser import (
    AccountClass,
    is_monarch_filename,
    parse_monarch_csv,
)

HEADER = "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags\n"


def _csv(*rows: str) -> str:
    return HEADER + "\n".join(rows) + "\n"


def test_header_validation_rejects_missing_columns() -> None:
    text = "Date,Amount\n2025-05-06,-10.00\n"
    result = parse_monarch_csv(text)
    assert result.header_ok is False
    assert result.rows == []
    assert any("missing required column" in w.lower() for w in result.warnings)


def test_parses_basic_row_and_keeps_amount_sign() -> None:
    text = _csv(
        "2025-05-06,No Frills,Groceries,Scotia Momentum VISA Infinite (...5011),COSIMO'S NO FRILLS #3659,,-155.06,"
    )
    result = parse_monarch_csv(text)
    assert result.header_ok
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.occurred_on.isoformat() == "2025-05-06"
    assert row.merchant == "No Frills"
    assert row.category == "Groceries"
    assert row.amount == Decimal("-155.06")
    assert row.account_class == AccountClass.DEBT
    assert row.currency == "CAD"
    assert row.account_last4 == "5011"


def test_skips_monarch_pseudo_accounts() -> None:
    text = _csv(
        "2025-05-05,Interest Payment,Credit Card Payment,Transfer,INTEREST,,5.25,",
        "2025-05-05,Paycheck,Paychecks,Income,,,3000.00,",
        "2025-05-05,Something,Uncategorized,Uncategorized,,,10.00,",
    )
    result = parse_monarch_csv(text)
    assert len(result.rows) == 0
    assert result.skipped_pseudo == 3


def test_classifies_non_cad_usd_accounts_as_foreign() -> None:
    # Canopy is CAD + USD only. Any other currency prefix is skipped.
    text = _csv(
        "2025-05-06,Shopping,Shopping,EUR account (...0991),IKEA EUR,,-15.00,",
        "2025-05-06,Cafe,Restaurants,JPY account (...9625),Tokyo coffee,,-500,",
        "2025-05-06,Shop,Shopping,GBP account (...1234),UK shop,,-12.00,",
        "2025-05-06,Store,Shopping,BRL account (...9988),Brasil store,,-100.00,",
        "2025-05-06,Tea,Restaurants,TRY account (...3333),Istanbul tea,,-50.00,",
    )
    result = parse_monarch_csv(text)
    assert len(result.rows) == 0
    assert result.skipped_foreign == 5


def test_usd_accounts_are_imported_as_cad_peers() -> None:
    # USD is first-class in Canopy now. These rows must be kept, with
    # currency=USD and the correct cash/debt classification.
    text = _csv(
        "2025-05-06,Amazon,Shopping,USD account (...2015),AMZN,,-20.00,",
        "2025-05-06,Card,Shopping,Credit Card USA (...5305),US Amazon,,-10.00,",
        "2025-05-06,Fees,Fees,USA Checking (...4321),raw,,-5.00,",
    )
    result = parse_monarch_csv(text)
    assert result.skipped_foreign == 0
    assert len(result.rows) == 3
    by_label = {r.account_label: r for r in result.rows}
    assert by_label["USD account (...2015)"].account_class == AccountClass.CASH
    assert by_label["USD account (...2015)"].currency == "USD"
    assert by_label["Credit Card USA (...5305)"].account_class == AccountClass.DEBT
    assert by_label["Credit Card USA (...5305)"].currency == "USD"
    assert by_label["USA Checking (...4321)"].account_class == AccountClass.CASH
    assert by_label["USA Checking (...4321)"].currency == "USD"


def test_individual_without_investing_keyword_is_not_investment() -> None:
    # Regression: bare "individual" in inv_markers misclassified many bank
    # labels (e.g. credit/cash) as INVESTMENT → Assets hidden from /v1/accounts.
    # Removing that substring left "Individual (...)" as UNKNOWN, which the
    # importer skips entirely — also empty Accounts. Treat (...)-style labels
    # as cash.
    text = _csv(
        "2025-12-01,Store,Shopping,Individual (...52003),RAW,,-10.00,",
    )
    result = parse_monarch_csv(text)
    assert result.header_ok and len(result.rows) == 1
    assert result.rows[0].account_class == AccountClass.CASH


def test_individual_investing_stays_investment() -> None:
    # "Individual Investing (...)" must not match the Individual-(... chequing heuristic.
    text = _csv(
        "2025-12-01,Buy,Transfer,Individual Investing (...2015),raw,,100.00,",
    )
    result = parse_monarch_csv(text)
    assert len(result.rows) == 1
    assert result.rows[0].account_class == AccountClass.INVESTMENT


def test_amex_label_classified_as_debt() -> None:
    text = _csv(
        "2025-12-01,Store,Shopping,American Express (...1001),RAW,,-12.34,",
    )
    result = parse_monarch_csv(text)
    assert len(result.rows) == 1
    assert result.rows[0].account_class == AccountClass.DEBT


def test_classifies_account_families() -> None:
    text = _csv(
        "2025-05-06,A,x,RBC Day to Day Banking (...8813),raw,,-10.00,",
        "2025-05-06,B,x,Find & Save (...4736),raw,,-5.00,",
        "2025-05-06,C,x,Scotia Momentum VISA Infinite (...5011),raw,,-20.00,",
        "2025-05-06,D,x,Credit Line (...5001),raw,,-50.00,",
        "2025-05-06,E,x,MANAGED_TFSA (...DqRQ),raw,,10.28,",
        "2025-05-06,F,x,SELF_DIRECTED_RRSP (...xhBg),raw,,5.00,",
        "2025-05-06,G,x,CASH (...1s1h),raw,,15.00,",
        "2025-05-06,H,x,CanadaLife DPSP,raw,,1000.00,",
    )
    result = parse_monarch_csv(text)
    classes = [r.account_class for r in result.rows]
    # 3 investment (TFSA, RRSP, DPSP), 3 cash (Day to Day, Find & Save,
    # "CASH (...1s1h)"), 2 debt (VISA, Credit Line).
    assert classes.count(AccountClass.INVESTMENT) == 3
    assert classes.count(AccountClass.CASH) == 3
    assert classes.count(AccountClass.DEBT) == 2
    assert classes.count(AccountClass.UNKNOWN) == 0


def test_extracts_last4_variants() -> None:
    # "USA Direct Checking" would be filtered as FOREIGN, so use CAD
    # labels to verify the last4 regex variants.
    text = _csv(
        "2025-05-06,A,x,Checking (....8120),raw,,-1.00,",  # 4 dots
        "2025-05-06,B,x,MANAGED_TFSA (...DqRQ),raw,,1.00,",  # alphanumeric
        "2025-05-06,C,x,SELF_DIRECTED_CRYPTO (...-5g0),raw,,1.00,",  # with dash
    )
    result = parse_monarch_csv(text)
    assert [r.account_last4 for r in result.rows] == ["8120", "DqRQ", "-5g0"]


def test_is_monarch_filename() -> None:
    assert is_monarch_filename("monarch-transactions-123-abc.csv")
    assert is_monarch_filename("Monarch-Transactions-xyz.CSV")
    assert not is_monarch_filename("TFSA-monthly-statement-transactions-X-2025-12-01.csv")
    assert not is_monarch_filename("random.csv")
