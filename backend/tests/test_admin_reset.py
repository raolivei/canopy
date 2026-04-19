"""Tests for the admin data-reset service.

The FastAPI routing layer is exercised indirectly via the underlying
service; the endpoint itself is a thin wrapper adding header validation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability, LiabilityType
from backend.db.models.transaction import Transaction, TransactionType
from backend.services.admin import reset_all_data


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def _seed(db: Session) -> None:
    asset = Asset(
        symbol="TEST-BROKERAGE",
        name="Test Brokerage",
        asset_type=AssetType.RETIREMENT_TFSA,
        currency="CAD",
    )
    liab = Liability(
        name="Test Card",
        institution="Test Bank",
        liability_type=LiabilityType.CREDIT_CARD,
        currency="CAD",
        current_balance=Decimal("500"),
    )
    tx = Transaction(
        description="seeded",
        amount=Decimal("10"),
        currency="CAD",
        type=TransactionType.EXPENSE.value,
        date=datetime(2026, 4, 1),
    )
    db.add_all([asset, liab, tx])
    db.commit()


def test_reset_all_data_clears_every_table(db: Session) -> None:
    _seed(db)
    assert db.query(Asset).count() == 1
    assert db.query(Liability).count() == 1
    assert db.query(Transaction).count() == 1

    report = reset_all_data(db)
    db.commit()

    assert db.query(Asset).count() == 0
    assert db.query(Liability).count() == 0
    assert db.query(Transaction).count() == 0
    assert report.total >= 3
    # Every seeded table appears in the report (even as zero).
    assert "assets" in report.deleted
    assert "liabilities" in report.deleted
    assert "transactions" in report.deleted


def test_reset_all_data_is_idempotent(db: Session) -> None:
    _seed(db)
    reset_all_data(db)
    db.commit()

    second = reset_all_data(db)
    db.commit()

    assert second.total == 0
    assert all(v == 0 for v in second.deleted.values())


def test_reset_all_data_preserves_schema(db: Session) -> None:
    _seed(db)
    reset_all_data(db)
    db.commit()

    # Schema is intact: we can still insert new rows after reset.
    asset = Asset(
        symbol="FRESH-ACCOUNT",
        name="Fresh Account",
        asset_type=AssetType.BANK_ACCOUNT,
        currency="CAD",
    )
    db.add(asset)
    db.commit()

    assert db.query(Asset).count() == 1
