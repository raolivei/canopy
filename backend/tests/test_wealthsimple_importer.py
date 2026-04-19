"""Integration tests for the Wealthsimple CSV importer.

Uses an in-memory SQLite DB with ``ARRAY``/``JSONB`` columns compiled to
``TEXT``/``JSON`` (see ``conftest.py``). Only exercises the importer's
pure ingestion logic - the FastAPI layer is not involved here.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset
from backend.db.models.imported_event import ImportedEvent
from backend.db.models.liability import Liability, LiabilityBalanceHistory
from backend.db.models.lot import Lot
from backend.db.models.transaction import Transaction
from backend.services.wealthsimple.importer import WealthsimpleImporter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


# Minimal synthetic CSVs (no PII)


TFSA_CSV = (
    '"date","transaction","description","amount","balance","currency"\n'
    '"2025-12-02","DIV","ZAG - BMO Aggregate Bond Index ETF: Cash dividend distribution, received on 2025-12-02, record date of 2025-11-26","3.97","3.97","CAD"\n'
    '"2025-12-10","BUY","QCN - Mackenzie Canadian Equity Index ETF Series E: Bought 0.2994 shares at $191.55 per share (executed at 2025-12-10)","-57.35","-53.38","CAD"\n'
    '"2025-12-31","FEE","Management fees for period 2025-12-01 to 2025-12-31 (executed at 2025-12-31)","-5.00","-58.38","CAD"\n'
)


CHEQUING_CSV = (
    '"date","transaction","description","amount","balance","currency"\n'
    '"2025-12-12","AFT_IN","Direct deposit from MOMENTIVE CANAD","4000.00","4000.00","CAD"\n'
    '"2025-12-22","EFTOUT","Withdrawal","-1000.00","3000.00","CAD"\n'
)


CC_CSV = (
    '"transaction_date","post_date","type","details","amount","currency"\n'
    '"2025-12-10","2025-12-11","Purchase","AMAZON* B22LL3VV1","16.25","CAD"\n'
    '"2025-12-20","2025-12-20","Refund initiated","AMAZON* B286203X2","-10.00","CAD"\n'
)


LOC_CSV = (
    '"date","transaction","description","amount","balance","currency"\n'
    '"2026-03-08","TRFOUTTF","Tax-free money transfer out of the account","-2000.00","1000.00","CAD"\n'
    '"2026-03-17","TRFOUTTF","Tax-free money transfer out of the account","-1000.00","0.00","CAD"\n'
)


DIRECT_INDEXING_CSV = (
    '"date","transaction","description","amount","balance","currency"\n'
    '"2026-03-04","BUY","CRM - Salesforce Inc.: Bought 0.0371 shares at $192.11 per share (executed at 2026-03-03)","-9.75","-9.75","CAD"\n'
)


def _tfsa_file() -> tuple[str, str]:
    return (
        "TFSA-monthly-statement-transactions-HQB2DBYK0CAD-2025-12-01.csv",
        TFSA_CSV,
    )


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def test_tfsa_creates_account_asset_and_transactions(db: Session) -> None:
    WealthsimpleImporter(db).ingest([_tfsa_file()])
    db.commit()

    asset = db.execute(select(Asset).where(Asset.symbol == "WS:HQB2DBYK0CAD")).scalar_one()
    assert asset.name == "TFSA"
    assert asset.sync_source == "wealthsimple"
    assert asset.asset_type.value == "retirement_tfsa"

    tx_count = db.execute(select(Transaction)).scalars().all()
    assert len(tx_count) == 3


def test_buy_row_creates_lot_and_ticker_asset(db: Session) -> None:
    WealthsimpleImporter(db).ingest([_tfsa_file()])
    db.commit()

    ticker_asset = db.execute(select(Asset).where(Asset.symbol == "QCN")).scalar_one()
    lots = db.execute(select(Lot).where(Lot.asset_id == ticker_asset.id)).scalars().all()
    assert len(lots) == 1
    assert lots[0].quantity == Decimal("0.2994")
    assert lots[0].price_per_unit == Decimal("191.55")


def test_chequing_file_creates_bank_asset(db: Session) -> None:
    WealthsimpleImporter(db).ingest(
        [
            (
                "Chequing-monthly-statement-transactions-WK15SYK37CAD-2025-12-01.csv",
                CHEQUING_CSV,
            )
        ]
    )
    db.commit()
    asset = db.execute(select(Asset).where(Asset.symbol == "WS:WK15SYK37CAD")).scalar_one()
    assert asset.asset_type.value == "bank_checking"


def test_credit_card_creates_liability_and_running_balance(db: Session) -> None:
    WealthsimpleImporter(db).ingest([("credit-card-statement-transactions-2025-12-01.csv", CC_CSV)])
    db.commit()

    liab = db.execute(select(Liability).where(Liability.institution == "Wealthsimple")).scalar_one()
    assert liab.liability_type == "credit_card"
    # 16.25 - 10.00 = 6.25 delta against opening_balance=0
    assert liab.current_balance == Decimal("6.25")


def test_loc_creates_liability_and_uses_balance_column(db: Session) -> None:
    WealthsimpleImporter(db).ingest(
        [
            (
                "Portfolio line of credit-monthly-statement-transactions-HQB2DBL08CAD-2026-03-01.csv",
                LOC_CSV,
            )
        ]
    )
    db.commit()
    liab = db.execute(select(Liability).where(Liability.liability_type == "line_of_credit")).scalar_one()
    # The LOC's final balance column reads 0.00 (all transferred out)
    assert liab.current_balance == Decimal("0.00")
    snapshots = db.execute(select(LiabilityBalanceHistory)).scalars().all()
    assert len(snapshots) >= 1


def test_direct_indexing_is_skipped(db: Session) -> None:
    summary = WealthsimpleImporter(db).ingest(
        [
            (
                "Direct Indexing-monthly-statement-transactions-WZ0BM4C09CAD-2026-03-01.csv",
                DIRECT_INDEXING_CSV,
            )
        ]
    )
    db.commit()
    assert summary.files[0].skipped is True
    # Nothing was written
    assert db.execute(select(Asset)).scalars().all() == []
    assert db.execute(select(Transaction)).scalars().all() == []
    assert db.execute(select(Lot)).scalars().all() == []


# ---------------------------------------------------------------------------
# End-of-statement snapshots
# ---------------------------------------------------------------------------


def test_tfsa_end_of_statement_snapshot_matches_last_row(db: Session) -> None:
    WealthsimpleImporter(db).ingest([_tfsa_file()])
    db.commit()
    snap = db.execute(select(AccountBalanceHistory)).scalars().all()
    assert len(snap) == 1
    # Statement's last row balance was -58.38; snapshot as_of = last day of Dec 2025
    assert snap[0].balance == Decimal("-58.38")
    assert snap[0].as_of_date.isoformat() == "2025-12-31"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_reimporting_same_file_writes_no_new_rows(db: Session) -> None:
    importer = WealthsimpleImporter(db)
    importer.ingest([_tfsa_file()])
    db.commit()

    tx_before = len(db.execute(select(Transaction)).scalars().all())
    events_before = len(db.execute(select(ImportedEvent)).scalars().all())

    # Fresh importer instance: no in-memory cache, must rely on the DB ledger
    importer2 = WealthsimpleImporter(db)
    summary = importer2.ingest([_tfsa_file()])
    db.commit()

    tx_after = len(db.execute(select(Transaction)).scalars().all())
    events_after = len(db.execute(select(ImportedEvent)).scalars().all())

    assert tx_after == tx_before
    assert events_after == events_before
    assert summary.files[0].rows_duplicate == summary.files[0].rows_seen


# ---------------------------------------------------------------------------
# Multi-file: full net-worth picture from one drop
# ---------------------------------------------------------------------------


def test_multi_file_drop_classifies_all_three(db: Session) -> None:
    summary = WealthsimpleImporter(db).ingest(
        [
            _tfsa_file(),
            (
                "Chequing-monthly-statement-transactions-WK15SYK37CAD-2025-12-01.csv",
                CHEQUING_CSV,
            ),
            ("credit-card-statement-transactions-2025-12-01.csv", CC_CSV),
        ]
    )
    db.commit()

    kinds = [f.meta.account_class.value for f in summary.files]
    assert set(kinds) == {"investment", "cash", "debt"}
    assert summary.transactions_added > 0
    assert summary.account_snapshots_added >= 1
    assert summary.liability_snapshots_added >= 1
