"""Regression: ``GET /v1/accounts`` includes legacy Monarch ``other`` cash assets."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.api.accounts import list_accounts
from backend.db.base import Base
from backend.db.models.asset import Asset, AssetType


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def test_list_accounts_includes_csv_import_other_when_monarch_says_cash(db: Session) -> None:
    db.add(
        Asset(
            symbol="MONARCH-LEGACY",
            name="Individual (...52003)",
            asset_type=AssetType.OTHER,
            currency="CAD",
            institution="Imported from Monarch",
            sync_source="csv_import",
            current_price=Decimal("42.00"),
        )
    )
    db.commit()

    async def _run() -> object:
        with patch("backend.api.accounts.fx_service.ensure_latest_rate_cached", return_value=None):
            return await list_accounts(db)

    resp = asyncio.run(_run())

    names = {a.name for a in resp.accounts}
    assert "Individual (...52003)" in names


def test_list_accounts_excludes_csv_import_other_when_still_unknown(db: Session) -> None:
    db.add(
        Asset(
            symbol="MONARCH-UNK",
            name="Plaid Sync (...9999)",
            asset_type=AssetType.OTHER,
            currency="CAD",
            sync_source="csv_import",
        )
    )
    db.commit()

    async def _run() -> object:
        with patch("backend.api.accounts.fx_service.ensure_latest_rate_cached", return_value=None):
            return await list_accounts(db)

    resp = asyncio.run(_run())
    assert all("Plaid" not in a.name for a in resp.accounts)
