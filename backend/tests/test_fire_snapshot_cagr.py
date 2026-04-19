"""CAGR inference for FIRE from portfolio_snapshots."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.portfolio_snapshot import PortfolioSnapshot
from backend.services.fire_calculator import infer_annual_return_from_portfolio_snapshots


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def test_infer_cagr_none_when_single_snapshot(db: Session) -> None:
    db.add(
        PortfolioSnapshot(
            snapshot_date=date(2026, 1, 1),
            total_value=Decimal("100000"),
            total_cost_basis=Decimal("90000"),
        )
    )
    db.commit()
    rate, span = infer_annual_return_from_portfolio_snapshots(db)
    assert rate is None
    assert span is None


def test_infer_cagr_none_when_span_too_short(db: Session) -> None:
    d0 = date(2026, 1, 1)
    d1 = d0 + timedelta(days=30)
    db.add(
        PortfolioSnapshot(
            snapshot_date=d0,
            total_value=Decimal("100000"),
            total_cost_basis=Decimal("90000"),
        )
    )
    db.add(
        PortfolioSnapshot(
            snapshot_date=d1,
            total_value=Decimal("101000"),
            total_cost_basis=Decimal("90000"),
        )
    )
    db.commit()
    rate, span = infer_annual_return_from_portfolio_snapshots(db)
    assert rate is None
    assert span is None


def test_infer_cagr_positive_over_long_span(db: Session) -> None:
    d0 = date(2025, 1, 1)
    d1 = d0 + timedelta(days=365)
    db.add(
        PortfolioSnapshot(
            snapshot_date=d0,
            total_value=Decimal("100000"),
            total_cost_basis=Decimal("90000"),
        )
    )
    db.add(
        PortfolioSnapshot(
            snapshot_date=d1,
            total_value=Decimal("110000"),
            total_cost_basis=Decimal("90000"),
        )
    )
    db.commit()
    rate, span = infer_annual_return_from_portfolio_snapshots(db)
    assert rate is not None
    assert span == 365
    assert Decimal("0.05") < rate < Decimal("0.15")  # ~10% CAGR
