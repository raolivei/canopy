"""Multi-currency roll-up tests for the accounts API helpers.

We exercise the pure aggregation helpers rather than the FastAPI route
so the test stays focused on the maths and doesn't need a full
TestClient. The route just composes these helpers + a DB round trip.
"""

from __future__ import annotations

from decimal import Decimal

from backend.api.accounts import (
    AccountResponse,
    _combine_totals,
    _roll_up_by_currency,
)


def _acc(**kwargs) -> AccountResponse:
    """Build an AccountResponse with sensible defaults for the tests."""
    return AccountResponse(
        id=kwargs.pop("id", "asset:1"),
        name=kwargs.pop("name", "Test"),
        kind=kwargs.pop("kind"),
        balance=kwargs.pop("balance"),
        currency=kwargs.pop("currency", "CAD"),
        institution=kwargs.pop("institution", None),
    )


def test_roll_up_buckets_cash_and_debt_per_currency() -> None:
    accounts = [
        _acc(id="asset:1", kind="checking", balance=1_000.00, currency="CAD"),
        _acc(id="asset:2", kind="savings", balance=500.00, currency="CAD"),
        _acc(id="asset:3", kind="cash", balance=250.00, currency="USD"),
        _acc(id="liability:1", kind="credit", balance=200.00, currency="CAD"),
        _acc(id="liability:2", kind="line_of_credit", balance=50.00, currency="USD"),
    ]

    totals = _roll_up_by_currency(accounts)

    assert totals["CAD"].cash == 1_500.00
    assert totals["CAD"].debt == 200.00
    assert totals["CAD"].net == 1_300.00
    assert totals["USD"].cash == 250.00
    assert totals["USD"].debt == 50.00
    assert totals["USD"].net == 200.00


def test_roll_up_always_returns_cad_and_usd_even_when_empty() -> None:
    totals = _roll_up_by_currency([])
    assert totals["CAD"].cash == 0.0
    assert totals["CAD"].debt == 0.0
    assert totals["USD"].cash == 0.0
    assert totals["USD"].debt == 0.0


def test_combine_totals_converts_usd_into_cad_and_vice_versa() -> None:
    accounts = [
        _acc(id="asset:1", kind="checking", balance=1000.0, currency="CAD"),
        _acc(id="asset:2", kind="cash", balance=100.0, currency="USD"),
        _acc(id="liability:1", kind="credit", balance=50.0, currency="USD"),
    ]
    per_ccy = _roll_up_by_currency(accounts)

    combined = _combine_totals(per_ccy, Decimal("1.40"))

    # Combined CAD: CAD cash + (USD cash * rate) = 1000 + 140
    assert combined["CAD"].cash == 1140.0
    assert combined["CAD"].debt == 70.0  # 0 CAD debt + 50 USD * 1.40
    assert combined["CAD"].net == 1070.0

    # Combined USD: USD cash + (CAD cash / rate) = 100 + (1000 / 1.4)
    assert combined["USD"].cash == 100.0 + (1000.0 / 1.40)
    assert combined["USD"].debt == 50.0  # 50 USD + 0 CAD / 1.40
    assert combined["USD"].net == (100.0 + 1000.0 / 1.40) - 50.0


def test_combine_totals_with_missing_rate_treats_usd_as_zero() -> None:
    """When the FX cache is empty the backend still returns a response.

    USD contributions drop to zero so aggregations stay self-consistent;
    the frontend surfaces the ``is_stale`` banner to explain why the
    combined total disagrees with the individual CAD and USD buckets.
    """
    accounts = [
        _acc(id="asset:1", kind="checking", balance=1000.0, currency="CAD"),
        _acc(id="asset:2", kind="cash", balance=100.0, currency="USD"),
    ]
    per_ccy = _roll_up_by_currency(accounts)

    combined = _combine_totals(per_ccy, None)

    # CAD slice: just the CAD side (USD contribution zeroed).
    assert combined["CAD"].cash == 1000.0
    # USD slice: just the USD side.
    assert combined["USD"].cash == 100.0


def test_combine_totals_is_symmetric_when_only_one_currency_is_present() -> None:
    """A CAD-only app (no USD accounts yet) should have matching CAD-only views.

    Combined CAD and CAD-only should agree bit-for-bit; Combined USD is
    just CAD converted at the rate.
    """
    accounts = [
        _acc(id="asset:1", kind="checking", balance=2500.0, currency="CAD"),
    ]
    per_ccy = _roll_up_by_currency(accounts)
    combined = _combine_totals(per_ccy, Decimal("1.3800"))

    assert combined["CAD"].cash == per_ccy["CAD"].cash
    assert combined["CAD"].net == per_ccy["CAD"].net
    assert combined["USD"].cash == 2500.0 / 1.38


def test_latest_balances_pulls_from_account_balance_history() -> None:
    """Regression: the Accounts page was reading ``asset.current_price``
    (never populated by CSV imports) and rendering every account as $0.
    ``_latest_balances_by_asset`` must return the newest balance-history
    row per asset, matched on the asset's own currency.
    """
    from datetime import date

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from backend.api.accounts import _latest_balances_by_asset
    from backend.db.base import Base
    from backend.db.models.account_balance_history import AccountBalanceHistory
    from backend.db.models.asset import Asset, AssetType

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as db:
        chq = Asset(
            symbol="WS-CHQ",
            name="Wealthsimple Chequing",
            asset_type=AssetType.BANK_CHECKING,
            currency="CAD",
            institution="Wealthsimple",
            sync_source="wealthsimple",
        )
        tfsa = Asset(
            symbol="WS-TFSA",
            name="Wealthsimple TFSA",
            asset_type=AssetType.RETIREMENT_TFSA,
            currency="CAD",
            institution="Wealthsimple",
            sync_source="wealthsimple",
        )
        db.add_all([chq, tfsa])
        db.flush()

        db.add_all([
            AccountBalanceHistory(
                asset_id=chq.id,
                as_of_date=date(2026, 1, 31),
                balance=Decimal("100.00"),
                currency="CAD",
                source="wealthsimple_csv",
            ),
            AccountBalanceHistory(
                asset_id=chq.id,
                as_of_date=date(2026, 3, 31),
                balance=Decimal("1.61"),
                currency="CAD",
                source="wealthsimple_csv",
            ),
            # A USD sub-balance on a CAD-denominated TFSA should be
            # ignored for the Accounts-page "native" view.
            AccountBalanceHistory(
                asset_id=tfsa.id,
                as_of_date=date(2026, 3, 31),
                balance=Decimal("42.00"),
                currency="USD",
                source="wealthsimple_csv",
            ),
            AccountBalanceHistory(
                asset_id=tfsa.id,
                as_of_date=date(2026, 3, 31),
                balance=Decimal("500.00"),
                currency="CAD",
                source="wealthsimple_csv",
            ),
        ])
        db.flush()

        latest = _latest_balances_by_asset(db, [chq.id, tfsa.id])

        assert latest[chq.id][0] == Decimal("1.61")
        assert latest[chq.id][1] == date(2026, 3, 31)
        # TFSA: CAD row wins over the USD sub-balance.
        assert latest[tfsa.id][0] == Decimal("500.00")
        assert isinstance(latest[tfsa.id][1], date)
