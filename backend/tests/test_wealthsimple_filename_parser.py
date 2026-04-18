"""Tests for the Wealthsimple CSV filename parser."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.wealthsimple.filename_parser import (
    AccountClass,
    WsAccountKind,
    parse_filename,
)

CASES: list[tuple[str, WsAccountKind, AccountClass, str | None]] = [
    (
        "Chequing-monthly-statement-transactions-WK15SYK37CAD-2025-12-01.csv",
        WsAccountKind.CHEQUING,
        AccountClass.CASH,
        "WK15SYK37CAD",
    ),
    (
        "credit-card-statement-transactions-2025-12-01.csv",
        WsAccountKind.CREDIT_CARD,
        AccountClass.DEBT,
        None,
    ),
    (
        "Crypto-monthly-statement-transactions-H68611617CAD-2026-03-01.csv",
        WsAccountKind.CRYPTO,
        AccountClass.INVESTMENT,
        "H68611617CAD",
    ),
    (
        "Direct Indexing-monthly-statement-transactions-WZ0BM4C09CAD-2026-03-01.csv",
        WsAccountKind.DIRECT_INDEXING,
        AccountClass.SKIP,
        "WZ0BM4C09CAD",
    ),
    (
        "Emerging \U0001f1ee\U0001f1f3\U0001f1ef\U0001f1f5\U0001f1e7\U0001f1f7"
        "-monthly-statement-transactions-HQ7P9HR40CAD-2026-03-01.csv",
        WsAccountKind.EMERGING,
        AccountClass.INVESTMENT,
        "HQ7P9HR40CAD",
    ),
    (
        "FHSA-monthly-statement-transactions-WK2F1TR60CAD-2026-03-01.csv",
        WsAccountKind.FHSA,
        AccountClass.INVESTMENT,
        "WK2F1TR60CAD",
    ),
    (
        "Portfolio line of credit-monthly-statement-transactions-HQB2DBL08CAD-2026-03-01.csv",
        WsAccountKind.LINE_OF_CREDIT,
        AccountClass.DEBT,
        "HQB2DBL08CAD",
    ),
    (
        "Retirement \u26f1\ufe0f-monthly-statement-transactions-W88119545CAD-2025-12-01.csv",
        WsAccountKind.RRSP,
        AccountClass.INVESTMENT,
        "W88119545CAD",
    ),
    (
        "TFSA Long-monthly-statement-transactions-W880772K2CAD-2025-12-01.csv",
        WsAccountKind.TFSA_LONG,
        AccountClass.INVESTMENT,
        "W880772K2CAD",
    ),
    (
        "TFSA-monthly-statement-transactions-HQB2DBYK0CAD-2026-03-01.csv",
        WsAccountKind.TFSA,
        AccountClass.INVESTMENT,
        "HQB2DBYK0CAD",
    ),
]


@pytest.mark.parametrize("filename, kind, cls, account_number", CASES)
def test_parse_filename_classifies_correctly(
    filename: str,
    kind: WsAccountKind,
    cls: AccountClass,
    account_number: str | None,
) -> None:
    meta = parse_filename(filename)
    assert meta.account_kind is kind
    assert meta.account_class is cls
    assert meta.account_number == account_number
    # Every fixture encodes a statement start date in the filename
    assert isinstance(meta.statement_period_start, date)


def test_direct_indexing_is_marked_skip() -> None:
    meta = parse_filename(
        "Direct Indexing-monthly-statement-transactions-WZ0BM4C09CAD-2026-03-01.csv"
    )
    assert meta.is_skipped
    assert meta.skip_reason is not None
    assert "Direct Indexing" in meta.skip_reason


def test_unknown_filename_is_skipped() -> None:
    meta = parse_filename("bogus-export.csv")
    assert meta.account_kind is WsAccountKind.UNKNOWN
    assert meta.account_class is AccountClass.SKIP
    assert meta.skip_reason is not None


def test_path_prefix_is_stripped() -> None:
    meta = parse_filename(
        "/tmp/uploads/TFSA-monthly-statement-transactions-HQB2DBYK0CAD-2026-03-01.csv"
    )
    assert meta.account_kind is WsAccountKind.TFSA
    assert meta.filename.startswith("TFSA-")
