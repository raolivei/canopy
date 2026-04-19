"""End-to-end test for the multi-currency net-worth timeline.

Seeds a tiny portfolio with both CAD and USD sub-balances plus daily
BoC FX rates, then asserts that each point exposes the four
Questrade-style slices (CAD, USD, Combined CAD, Combined USD) with
the correct per-date FX conversion.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.api.wealthsimple_import import networth_timeline
from backend.db.base import Base
from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType
from backend.db.models.fx_rate import FxRate
from backend.db.models.liability import (
    Liability,
    LiabilityBalanceHistory,
    LiabilityStatus,
)


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def _seed_portfolio(db: Session) -> None:
    """Seed one TFSA (CAD + USD sub-balances) and one credit card (CAD).

    Timeline:

    * 2026-01-31 — TFSA CAD $1000, TFSA USD $500, VISA CAD -$200
    * 2026-02-28 — TFSA CAD $1100, TFSA USD $550, VISA CAD -$150

    FX rates:

    * 2026-01-31 USD/CAD = 1.35
    * 2026-02-28 USD/CAD = 1.40
    """
    tfsa = Asset(
        symbol="WS-TFSA",
        name="Wealthsimple TFSA",
        asset_type=AssetType.RETIREMENT_TFSA,
        currency="CAD",
        institution="Wealthsimple",
        sync_source="wealthsimple",
    )
    db.add(tfsa)
    visa = Liability(
        name="Scotia VISA",
        liability_type="credit_card",
        currency="CAD",
        institution="Scotiabank",
        status=LiabilityStatus.ACTIVE,
        current_balance=Decimal("150"),
    )
    db.add(visa)
    db.flush()

    rows = [
        AccountBalanceHistory(
            asset_id=tfsa.id,
            as_of_date=date(2026, 1, 31),
            balance=Decimal("1000"),
            currency="CAD",
            source="wealthsimple_csv",
        ),
        AccountBalanceHistory(
            asset_id=tfsa.id,
            as_of_date=date(2026, 1, 31),
            balance=Decimal("500"),
            currency="USD",
            source="wealthsimple_csv",
        ),
        AccountBalanceHistory(
            asset_id=tfsa.id,
            as_of_date=date(2026, 2, 28),
            balance=Decimal("1100"),
            currency="CAD",
            source="wealthsimple_csv",
        ),
        AccountBalanceHistory(
            asset_id=tfsa.id,
            as_of_date=date(2026, 2, 28),
            balance=Decimal("550"),
            currency="USD",
            source="wealthsimple_csv",
        ),
    ]
    db.add_all(rows)

    db.add_all(
        [
            LiabilityBalanceHistory(
                liability_id=visa.id,
                balance=Decimal("200"),
                recorded_at=datetime(2026, 1, 31, tzinfo=timezone.utc),
            ),
            LiabilityBalanceHistory(
                liability_id=visa.id,
                balance=Decimal("150"),
                recorded_at=datetime(2026, 2, 28, tzinfo=timezone.utc),
            ),
        ]
    )

    db.add_all(
        [
            FxRate(
                pair="USDCAD",
                as_of_date=date(2026, 1, 31),
                rate=Decimal("1.35"),
                source="bank_of_canada",
            ),
            FxRate(
                pair="USDCAD",
                as_of_date=date(2026, 2, 28),
                rate=Decimal("1.40"),
                source="bank_of_canada",
            ),
        ]
    )
    db.flush()


def test_timeline_emits_cad_usd_and_combined_slices_per_point(db: Session) -> None:
    _seed_portfolio(db)

    response = networth_timeline(db)

    assert len(response.points) == 2
    p1, p2 = response.points

    # --- Point 1: 2026-01-31 --------------------------------------------------
    # CAD slice: investments=1000 cash=0 debt=200 net=800
    assert p1.cad.investments == Decimal("1000")
    assert p1.cad.debt == Decimal("200")
    assert p1.cad.net_worth == Decimal("800")

    # USD slice: investments=500 debt=0 net=500
    assert p1.usd.investments == Decimal("500")
    assert p1.usd.debt == Decimal("0")
    assert p1.usd.net_worth == Decimal("500")

    # Combined CAD @ rate=1.35: CAD+USD*rate = 1000 + 500*1.35 = 1675; debt=200
    assert p1.combined_cad.investments == Decimal("1675.00")
    assert p1.combined_cad.debt == Decimal("200")
    assert p1.combined_cad.net_worth == Decimal("1475.00")

    # Combined USD @ rate=1.35: USD+CAD/rate; debt=0 + 200/1.35
    assert p1.combined_usd.investments == Decimal("500") + Decimal("1000") / Decimal(
        "1.35"
    )
    assert p1.combined_usd.debt == Decimal("200") / Decimal("1.35")

    assert p1.fx_rate == Decimal("1.35")

    # --- Point 2: 2026-02-28 --------------------------------------------------
    # Combined CAD @ rate=1.40: 1100 + 550*1.40 = 1870; debt=150
    assert p2.combined_cad.investments == Decimal("1870.00")
    assert p2.combined_cad.debt == Decimal("150")
    assert p2.combined_cad.net_worth == Decimal("1720.00")

    # Legacy top-level fields still mirror the CAD slice.
    assert p2.investments == p2.cad.investments
    assert p2.net_worth == p2.cad.net_worth

    assert p2.fx_rate == Decimal("1.40")


def test_timeline_falls_back_to_prior_rate_when_date_not_in_table(db: Session) -> None:
    """A balance point sitting between two FX observations uses the prior close."""
    _seed_portfolio(db)
    # Add a third balance point on a Sunday (no BoC publish); the
    # aggregator should carry forward the 2026-02-28 rate.
    tfsa = db.query(Asset).filter_by(symbol="WS-TFSA").one()
    db.add(
        AccountBalanceHistory(
            asset_id=tfsa.id,
            as_of_date=date(2026, 3, 1),  # Sunday
            balance=Decimal("1200"),
            currency="CAD",
            source="wealthsimple_csv",
        )
    )
    db.flush()

    response = networth_timeline(db)
    last = response.points[-1]
    assert last.date == date(2026, 3, 1)
    # Uses Friday 2026-02-28's rate = 1.40.
    assert last.fx_rate == Decimal("1.40")


def test_timeline_is_empty_when_no_balances(db: Session) -> None:
    response = networth_timeline(db)
    assert response.points == []
    assert response.latest_cad is None
