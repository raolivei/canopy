"""Tests for the FX service (Bank of Canada USD/CAD cache + conversion).

Network is stubbed via the ``http_get`` hook so the tests run fully
offline. Coverage focuses on the four behaviours the rest of the app
depends on:

* Exact-date lookup.
* Closest-prior fallback for weekends / holidays.
* Conversion math (CAD <-> USD) is correct and symmetric.
* ``ensure_latest_rate_cached`` writes through and handles BoC outages.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.fx_rate import FxRate
from backend.services import fx as fx_service


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


def _seed(session: Session, rows: list[tuple[str, str]]) -> None:
    for d_str, rate_str in rows:
        session.add(
            FxRate(
                pair="USDCAD",
                as_of_date=date.fromisoformat(d_str),
                rate=Decimal(rate_str),
                source="bank_of_canada",
            )
        )
    session.flush()


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def test_get_rate_on_returns_exact_date(db: Session) -> None:
    _seed(db, [("2026-04-15", "1.3845"), ("2026-04-16", "1.3820")])

    assert fx_service.get_rate_on(db, date(2026, 4, 15)) == Decimal("1.3845")
    assert fx_service.get_rate_on(db, date(2026, 4, 16)) == Decimal("1.3820")


def test_get_rate_on_falls_back_to_most_recent_prior(db: Session) -> None:
    # BoC doesn't publish weekends — the Saturday / Sunday lookup
    # should return Friday's close.
    _seed(db, [("2026-04-17", "1.3800")])  # Friday

    assert fx_service.get_rate_on(db, date(2026, 4, 18)) == Decimal("1.3800")  # Sat
    assert fx_service.get_rate_on(db, date(2026, 4, 19)) == Decimal("1.3800")  # Sun
    assert fx_service.get_rate_on(db, date(2026, 4, 20)) == Decimal("1.3800")  # Mon


def test_get_rate_on_returns_none_when_table_is_empty_or_too_recent(
    db: Session,
) -> None:
    assert fx_service.get_rate_on(db, date(2026, 4, 18)) is None

    _seed(db, [("2026-04-18", "1.3800")])
    # Asking for a date *earlier* than everything in the table: there
    # is no prior observation to fall back to.
    assert fx_service.get_rate_on(db, date(2026, 4, 17)) is None


def test_get_latest_rate_returns_newest_row(db: Session) -> None:
    _seed(
        db,
        [
            ("2026-04-10", "1.3700"),
            ("2026-04-14", "1.3750"),
            ("2026-04-11", "1.3720"),
        ],
    )
    latest = fx_service.get_latest_rate(db)
    assert latest is not None
    assert latest.as_of_date == date(2026, 4, 14)
    assert latest.rate == Decimal("1.3750")


def test_is_stale_thresholds() -> None:
    today = date(2026, 4, 18)
    fresh = FxRate(
        pair="USDCAD", as_of_date=date(2026, 4, 17), rate=Decimal("1"), source="x"
    )
    stale = FxRate(
        pair="USDCAD", as_of_date=date(2026, 4, 10), rate=Decimal("1"), source="x"
    )

    assert fx_service.is_stale(None, today=today) is True
    assert fx_service.is_stale(fresh, today=today) is False
    assert fx_service.is_stale(stale, today=today) is True


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


def test_convert_usd_to_cad_multiplies() -> None:
    out = fx_service.convert(
        Decimal("100"),
        from_ccy="USD",
        to_ccy="CAD",
        usd_cad_rate=Decimal("1.3800"),
    )
    assert out == Decimal("138.00")


def test_convert_cad_to_usd_divides() -> None:
    out = fx_service.convert(
        Decimal("138"),
        from_ccy="CAD",
        to_ccy="USD",
        usd_cad_rate=Decimal("1.3800"),
    )
    # Tolerate Decimal division representation — check equality via
    # subtraction to avoid trailing-zero mismatches.
    assert out - Decimal("100") == Decimal("0")


def test_convert_same_currency_is_passthrough() -> None:
    for ccy in ("CAD", "USD"):
        out = fx_service.convert(
            Decimal("42"),
            from_ccy=ccy,
            to_ccy=ccy,
            usd_cad_rate=Decimal("0"),
        )
        assert out == Decimal("42")


def test_convert_rejects_unsupported_currencies() -> None:
    with pytest.raises(ValueError):
        fx_service.convert(
            Decimal("1"),
            from_ccy="EUR",
            to_ccy="CAD",
            usd_cad_rate=Decimal("1.4"),
        )


# ---------------------------------------------------------------------------
# Warm from Bank of Canada
# ---------------------------------------------------------------------------


def _fake_boc_payload(observations: list[tuple[str, str]]) -> dict:
    """Return a BoC Valet-shaped JSON payload for ``observations``."""
    return {
        "observations": [
            {"d": d_str, "FXUSDCAD": {"v": v_str}} for d_str, v_str in observations
        ]
    }


def test_ensure_latest_rate_cached_hits_boc_when_empty(db: Session) -> None:
    calls: list[str] = []

    def fake_get(url: str) -> dict:
        calls.append(url)
        return _fake_boc_payload(
            [
                ("2026-04-16", "1.3820"),
                ("2026-04-17", "1.3800"),
            ]
        )

    latest = fx_service.ensure_latest_rate_cached(db, http_get=fake_get)
    assert latest is not None
    assert latest.as_of_date == date(2026, 4, 17)
    assert latest.rate == Decimal("1.3800")
    assert len(calls) == 1
    # Row was actually written.
    stored = db.query(FxRate).count()
    assert stored == 2


def test_ensure_latest_rate_cached_skips_fetch_when_fresh(db: Session) -> None:
    # Seed today's rate; the service shouldn't call out to BoC.
    today = date.today()
    _seed(db, [(today.isoformat(), "1.3800")])

    def fake_get(url: str) -> dict:  # pragma: no cover - must not fire
        raise AssertionError("BoC should not be called when cache is fresh")

    latest = fx_service.ensure_latest_rate_cached(db, http_get=fake_get)
    assert latest is not None
    assert latest.as_of_date == today


def test_ensure_latest_rate_cached_survives_boc_outage(db: Session) -> None:
    # Seed a stale-but-usable row; BoC is unreachable.
    stale_day = date.today() - timedelta(days=30)
    _seed(db, [(stale_day.isoformat(), "1.3500")])

    def fake_get(url: str) -> dict:
        raise RuntimeError("simulated outage")

    latest = fx_service.ensure_latest_rate_cached(db, http_get=fake_get)
    # Degrades gracefully: caller gets the stale row, ``is_stale`` will
    # tell the frontend to show a banner.
    assert latest is not None
    assert latest.as_of_date == stale_day
    assert fx_service.is_stale(latest) is True


def test_ensure_latest_rate_cached_upserts_existing_dates(db: Session) -> None:
    # Seed a stale row so ``is_stale()`` forces the fetch path. We also
    # return a corrected value for that same date, verifying the UPSERT
    # updates rather than inserts a duplicate.
    stale_day = date.today() - timedelta(days=30)
    _seed(db, [(stale_day.isoformat(), "1.3700")])

    def fake_get(url: str) -> dict:
        return _fake_boc_payload([(stale_day.isoformat(), "1.3800")])

    latest = fx_service.ensure_latest_rate_cached(db, http_get=fake_get)
    assert latest is not None
    assert latest.rate == Decimal("1.3800")  # updated, not duplicated
    assert db.query(FxRate).count() == 1
