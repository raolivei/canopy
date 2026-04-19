"""Tests for the Monarch importer - end to end with SQLite.

Covers:

* Autocreate of assets and liabilities from unseen account labels.
* Canonical-hash dedup inside a single file (Layer 2, same source).
* Cross-source dedup: a Wealthsimple-sourced transaction already in the
  ledger blocks a Monarch row with the same (entity, date, amount)
  triple (Layer 2 across sources).
* Per-account cutover: once Wealthsimple-sourced transactions exist for
  an entity, Monarch rows on or after ``min(ws.date)`` for that entity
  are dropped as ``skipped_ws_covered`` (Layer 1).
* Foreign-currency and pseudo accounts are skipped.
* Re-uploading the same file is a no-op (``skipped_source_dup``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.asset import Asset, AssetType
from backend.db.models.imported_event import ImportedEvent
from backend.db.models.liability import Liability
from backend.db.models.transaction import Transaction
from backend.services.canonical_hash import (
    canonical_event_hash,
    entity_key_for_asset,
)
from backend.services.monarch.importer import MonarchImporter

HEADER = "Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags\n"


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def _file(*rows: str, filename: str = "monarch-transactions-x.csv") -> tuple[str, str]:
    return filename, HEADER + "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
# Autocreate + basic flow
# ---------------------------------------------------------------------------


def test_autocreates_assets_and_liabilities_and_writes_transactions(db: Session) -> None:
    f = _file(
        "2024-01-05,No Frills,Groceries,Scotia Momentum VISA Infinite (...5011),raw,,-50.00,",
        "2024-01-06,Payroll,Paychecks,RBC Day to Day Banking (...8813),raw,,2500.00,",
        "2024-01-07,Managed Buy,Transfer,MANAGED_TFSA (...DqRQ),raw,,100.00,",
    )
    summary = MonarchImporter(db).ingest([f])
    db.commit()

    assert summary.transactions_added == 3
    # 2 assets (chequing + TFSA), 1 liability (Scotia)
    assets = db.execute(select(Asset)).scalars().all()
    liabs = db.execute(select(Liability)).scalars().all()
    assert {a.asset_type for a in assets} == {
        AssetType.BANK_CHECKING,
        AssetType.RETIREMENT_TFSA,
    }
    assert len(liabs) == 1
    assert liabs[0].account_number_last4 == "5011"

    # Every Transaction got an ImportedEvent with both hashes populated
    events = db.execute(select(ImportedEvent)).scalars().all()
    assert len(events) == 3
    assert all(e.source == "monarch_csv" for e in events)
    assert all(e.canonical_hash is not None for e in events)


def test_reimporting_same_file_is_idempotent(db: Session) -> None:
    f = _file(
        "2024-01-05,No Frills,Groceries,Scotia Momentum VISA Infinite (...5011),raw,,-50.00,",
    )
    MonarchImporter(db).ingest([f])
    db.commit()

    summary = MonarchImporter(db).ingest([f])
    db.commit()

    assert summary.transactions_added == 0
    # Row shows up once in source_dup *or* canonical_dup (either is fine -
    # whichever check fires first). What matters is no second Transaction.
    assert len(db.execute(select(Transaction)).scalars().all()) == 1
    rep = summary.files[0]
    assert rep.skipped_source_dup + rep.skipped_canonical_dup == 1


# ---------------------------------------------------------------------------
# Layer 1: per-account Wealthsimple cutover
# ---------------------------------------------------------------------------


def test_layer1_cutover_drops_monarch_rows_in_ws_window(db: Session) -> None:
    # Seed a pre-existing WS-sourced Transaction on the same account name
    # that Monarch will resolve to (autocreate produces name == label, so
    # we create the WS asset with the same label to simulate a merge).
    asset = Asset(
        symbol="WS-TFSA",
        name="MANAGED_TFSA (...DqRQ)",
        asset_type=AssetType.RETIREMENT_TFSA,
        currency="CAD",
    )
    db.add(asset)
    db.flush()

    ws_tx = Transaction(
        description="Managed Buy",
        amount=Decimal("50.00"),
        currency="CAD",
        type="buy",
        date=datetime(2024, 6, 1, tzinfo=timezone.utc),
        account="MANAGED_TFSA (...DqRQ)",
        import_source="wealthsimple_csv",
    )
    db.add(ws_tx)
    db.commit()

    # Monarch file: one row before the WS window, one on the cutoff, one after.
    f = _file(
        "2024-05-31,Managed Buy,Transfer,MANAGED_TFSA (...DqRQ),raw,,10.00,",
        "2024-06-01,Managed Buy,Transfer,MANAGED_TFSA (...DqRQ),raw,,20.00,",
        "2024-07-01,Managed Buy,Transfer,MANAGED_TFSA (...DqRQ),raw,,30.00,",
    )
    summary = MonarchImporter(db).ingest([f])
    db.commit()

    rep = summary.files[0]
    assert rep.imported == 1  # only 2024-05-31 survives
    assert rep.skipped_ws_covered == 2

    monarch_rows = db.execute(select(Transaction).where(Transaction.import_source == "monarch_csv")).scalars().all()
    assert [t.date.date().isoformat() for t in monarch_rows] == ["2024-05-31"]


# ---------------------------------------------------------------------------
# Layer 2: canonical-hash backstop (cross-source)
# ---------------------------------------------------------------------------


def test_layer2_canonical_hash_blocks_cross_source_duplicate(db: Session) -> None:
    """Layer 2 catches duplicates that Layer 1 misses.

    Scenario: a canonical_hash for (entity, 2024-04-10, 42.00) is already
    in the ledger from a prior ingest, but there is no current WS
    ``Transaction`` bearing that entity's name - so Layer 1's cutover
    query returns ``None`` and lets the row through. Layer 2 then
    consults ``imported_events.canonical_hash`` and blocks it.
    """
    asset = Asset(
        symbol="WS-ASSET",
        name="RBC Day to Day Banking (...8813)",
        asset_type=AssetType.BANK_CHECKING,
        currency="CAD",
    )
    db.add(asset)
    db.flush()

    when = datetime(2024, 4, 10, tzinfo=timezone.utc).date()
    amount = Decimal("42.00")

    # Seed ONLY an ImportedEvent - no matching Transaction - so the
    # Layer-1 cutoff query for this account returns None.
    db.add(
        ImportedEvent(
            hash="ws-source-hash",
            canonical_hash=canonical_event_hash(entity_key_for_asset(asset.id), when, amount),
            source="wealthsimple_csv",
            target_table="transactions",
            target_id=None,
        )
    )
    db.commit()

    f = _file(
        # same (entity, date, amount) as seeded canonical - blocked by Layer 2
        "2024-04-10,Payroll,Paychecks,RBC Day to Day Banking (...8813),raw,,42.00,",
        # unrelated row, same account, different amount - allowed
        "2024-03-01,Coffee,Restaurants,RBC Day to Day Banking (...8813),raw,,-4.50,",
    )
    summary = MonarchImporter(db).ingest([f])
    db.commit()

    rep = summary.files[0]
    assert rep.imported == 1
    assert rep.skipped_canonical_dup == 1
    assert rep.skipped_ws_covered == 0


# ---------------------------------------------------------------------------
# Foreign / pseudo accounts
# ---------------------------------------------------------------------------


def test_foreign_and_pseudo_accounts_are_skipped_not_imported(db: Session) -> None:
    # Canopy is CAD + USD only: EUR / BRL / JPY / GBP / TRY are foreign.
    # Pseudo accounts (Transfer / Income / Uncategorized) are also skipped.
    f = _file(
        "2024-01-05,A,Income,Transfer,raw,,5.00,",
        "2024-01-05,B,Shopping,EUR account (...0991),raw,,-5.00,",
        "2024-01-05,C,Shopping,BRL account (...9988),raw,,-100.00,",
        "2024-01-05,D,Groceries,RBC Day to Day Banking (...8813),raw,,-25.00,",
    )
    summary = MonarchImporter(db).ingest([f])
    db.commit()

    rep = summary.files[0]
    assert rep.imported == 1
    assert rep.skipped_pseudo == 1
    assert rep.skipped_foreign == 2


def test_usd_accounts_autocreate_with_usd_currency(db: Session) -> None:
    # USD chequing and USD credit card are first-class in Canopy.
    # Autocreated entities inherit the row's currency, not a hardcoded CAD.
    f = _file(
        "2024-02-05,Amazon,Shopping,USD account (...2015),AMZN,,-20.00,",
        "2024-02-06,Amazon,Shopping,Credit Card USA (...5305),US AMZN,,-10.00,",
    )
    summary = MonarchImporter(db).ingest([f])
    db.commit()

    assert summary.transactions_added == 2
    usd_asset = db.execute(select(Asset).where(Asset.name == "USD account (...2015)")).scalar_one()
    assert usd_asset.currency == "USD"
    usd_liab = db.execute(
        select(Liability).where(Liability.name == "Credit Card USA (...5305)")
    ).scalar_one()
    assert usd_liab.currency == "USD"

    # Written transactions carry the same currency.
    txs = db.execute(select(Transaction)).scalars().all()
    assert {t.currency for t in txs} == {"USD"}
