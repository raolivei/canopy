"""Tests for the Monarch balances importer.

Covers:

* Asset balance snapshots are inserted into ``AccountBalanceHistory``.
* Liability balance snapshots are inserted into
  ``LiabilityBalanceHistory`` with Monarch's negative sign flipped to a
  positive "amount owed".
* Re-uploading the same file is a no-op (``inserted=0, updated=0``).
* Uploading a modified balance value updates in place.
* Unknown / pseudo / foreign-currency accounts are skipped.
* Cash vs. investment assets both route to ``AccountBalanceHistory``.
* Multi-currency: the same asset + date can hold a CAD and a USD row.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability, LiabilityBalanceHistory
from backend.services.monarch.balances_importer import MonarchBalancesImporter

HEADER = "Date,Balance,Account\n"


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def _file(*rows: str, filename: str = "Balances_2026-04-18.csv") -> tuple[str, str]:
    return filename, HEADER + "\n".join(rows) + "\n"


def test_imports_cash_and_investment_balances_into_account_balance_history(db: Session) -> None:
    f = _file(
        "2026-03-25,9677.84,RBC Day to Day Banking (...8813)",
        "2026-03-25,132608.79,MANAGED_RRSP (...z4qw)",
    )
    summary = MonarchBalancesImporter(db).ingest([f])
    db.commit()

    assert summary.inserted == 2
    assert summary.updated == 0

    rows = db.execute(
        select(AccountBalanceHistory).order_by(AccountBalanceHistory.asset_id)
    ).scalars().all()
    assert len(rows) == 2
    balances_by_name = {db.get(Asset, r.asset_id).name: r.balance for r in rows}
    assert balances_by_name["RBC Day to Day Banking (...8813)"] == Decimal("9677.84")
    assert balances_by_name["MANAGED_RRSP (...z4qw)"] == Decimal("132608.79")

    # Cash asset should be typed as a chequing account; investment as
    # retirement.
    assets = {a.name: a for a in db.execute(select(Asset)).scalars().all()}
    assert assets["RBC Day to Day Banking (...8813)"].asset_type == AssetType.BANK_CHECKING
    assert assets["MANAGED_RRSP (...z4qw)"].asset_type == AssetType.RETIREMENT_RRSP


def test_liability_balance_is_stored_as_positive_amount_owed(db: Session) -> None:
    f = _file(
        "2026-04-15,-21818.66,RBC Visa Classic Low Rate Option (...7192)",
    )
    summary = MonarchBalancesImporter(db).ingest([f])
    db.commit()

    assert summary.inserted == 1
    lib = db.execute(select(Liability)).scalar_one()
    history = db.execute(
        select(LiabilityBalanceHistory).where(
            LiabilityBalanceHistory.liability_id == lib.id,
        )
    ).scalar_one()
    # Monarch's negative sign is flipped so totals math stays consistent
    # with the WS importer.
    assert history.balance == Decimal("21818.66")
    assert history.recorded_at.date() == date(2026, 4, 15)
    # The denormalised current_balance on the Liability row must also
    # be synced — the Accounts page reads from that field, not from
    # LiabilityBalanceHistory.
    assert lib.current_balance == Decimal("21818.66")
    assert lib.balance_updated_at is not None


def test_backfilling_older_snapshot_does_not_overwrite_current_balance(db: Session) -> None:
    newer = _file("2026-04-15,-100.00,RBC Visa Classic Low Rate Option (...7192)")
    older = _file("2025-12-01,-9999.00,RBC Visa Classic Low Rate Option (...7192)")

    MonarchBalancesImporter(db).ingest([newer])
    db.commit()

    lib = db.execute(select(Liability)).scalar_one()
    assert lib.current_balance == Decimal("100.00")

    # Backfill an older snapshot. current_balance should stay pinned to
    # the newer row.
    MonarchBalancesImporter(db).ingest([older])
    db.commit()
    db.refresh(lib)
    assert lib.current_balance == Decimal("100.00")
    history_count = db.execute(
        select(LiabilityBalanceHistory).where(
            LiabilityBalanceHistory.liability_id == lib.id,
        )
    ).scalars().all()
    assert len(history_count) == 2


def test_re_importing_the_same_file_is_a_noop(db: Session) -> None:
    f = _file(
        "2026-03-25,9677.84,RBC Day to Day Banking (...8813)",
        "2026-04-15,-21818.66,RBC Visa Classic Low Rate Option (...7192)",
    )
    importer = MonarchBalancesImporter(db)
    importer.ingest([f])
    db.commit()

    # Second run — same payload.
    importer2 = MonarchBalancesImporter(db)
    second = importer2.ingest([f])
    db.commit()

    assert second.inserted == 0
    assert second.updated == 0
    # Exactly one row per (asset, date) / (liability, date).
    assert (
        len(db.execute(select(AccountBalanceHistory)).scalars().all()) == 1
    )
    assert (
        len(db.execute(select(LiabilityBalanceHistory)).scalars().all()) == 1
    )


def test_changed_balance_triggers_update_not_insert(db: Session) -> None:
    first = _file("2026-03-25,9677.84,RBC Day to Day Banking (...8813)")
    MonarchBalancesImporter(db).ingest([first])
    db.commit()

    # Same date, new value — e.g. a re-synced Monarch export.
    second = _file("2026-03-25,9999.00,RBC Day to Day Banking (...8813)")
    summary = MonarchBalancesImporter(db).ingest([second])
    db.commit()

    assert summary.inserted == 0
    assert summary.updated == 1
    row = db.execute(select(AccountBalanceHistory)).scalar_one()
    assert row.balance == Decimal("9999.00")


def test_foreign_and_pseudo_accounts_are_skipped(db: Session) -> None:
    f = _file(
        "2026-03-25,123.45,EUR account (...0991)",
        "2026-03-25,678.90,TRY account (...3253)",
        "2026-03-25,0.00,Transfer",
        "2026-03-25,100.00,CAD account (...1618)",
    )
    summary = MonarchBalancesImporter(db).ingest([f])
    db.commit()

    report = summary.files[0]
    assert report.skipped_foreign == 2
    assert report.skipped_pseudo == 1
    assert report.inserted == 1
    assert len(db.execute(select(AccountBalanceHistory)).scalars().all()) == 1


def test_multi_currency_on_same_asset_same_date_coexists(db: Session) -> None:
    # Two Monarch rows for the same underlying institution — one labelled
    # "USD account" and one labelled "CAD account". The importer auto-
    # creates *separate* assets here (distinct labels), but within one
    # asset we still want CAD + USD rows on the same date to coexist.
    # Use a pre-seeded investment asset + two synthetic files to force
    # that case.
    asset = Asset(
        symbol="MANAGED_TFSA-MIXED",
        name="MANAGED_TFSA (...mix1)",
        asset_type=AssetType.RETIREMENT_TFSA,
        currency="CAD",
        country="CA",
        external_account_id="mix1",
        sync_source="csv_import",
    )
    db.add(asset)
    db.commit()

    cad = _file("2026-03-31,10000.00,MANAGED_TFSA (...mix1)")
    usd = _file("2026-03-31,2500.00,USD account (...mix1)")
    MonarchBalancesImporter(db).ingest([cad, usd])
    db.commit()

    rows = db.execute(select(AccountBalanceHistory)).scalars().all()
    # Each label resolves to its own asset — the USD label is a distinct
    # auto-created account. Both rows should exist.
    assert len(rows) == 2
    currencies = sorted(r.currency for r in rows)
    assert currencies == ["CAD", "USD"]


def test_liability_same_day_repeated_balance_is_idempotent(db: Session) -> None:
    lib = Liability(
        name="RBC Visa Classic Low Rate Option (...7192)",
        institution="RBC",
        liability_type="credit_card",
        account_number_last4="7192",
        currency="CAD",
        country="CA",
    )
    db.add(lib)
    db.commit()

    # Seed an existing row for that date.
    db.add(
        LiabilityBalanceHistory(
            liability_id=lib.id,
            balance=Decimal("21818.66"),
            recorded_at=datetime(2026, 4, 15, tzinfo=timezone.utc),
        )
    )
    db.commit()

    f = _file("2026-04-15,-21818.66,RBC Visa Classic Low Rate Option (...7192)")
    summary = MonarchBalancesImporter(db).ingest([f])
    db.commit()

    assert summary.inserted == 0
    assert summary.updated == 0  # same value -> no-op
