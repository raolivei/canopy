"""Accounts API — cash + credit card + line of credit.

Reads directly from the tables populated by the Wealthsimple (and future
RBC) CSV importers so the Accounts page is always in sync with what was
imported.

Investments live on the Portfolio / Holdings pages and are intentionally
not returned here. This endpoint is for "money you spend from" (bank
accounts) and "money you owe" (credit cards, LOC, loans).

Currency views
--------------

Canopy supports the Questrade-style four-way view toggle (CAD, USD,
Combined CAD, Combined USD). The response always returns:

* ``accounts[]`` — every account with its *native* balance + currency.
* ``totals_by_currency`` — per-currency cash / debt / net roll-ups.
* ``totals_combined`` — cross-currency roll-ups expressed in both CAD
  and USD, so the UI can swap views without a second round trip.
* ``fx`` — the USD/CAD rate used for the combined math, with an
  ``is_stale`` flag for the frontend banner.

The top-level ``summary`` field is kept for back-compat with older
clients and mirrors the CAD-native section.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import desc, select

from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability
from backend.db.session import DbSession
from backend.services import fx as fx_service
from backend.services.fx import DISPLAY_FALLBACK_USDCAD

router = APIRouter(prefix="/v1/accounts", tags=["accounts"])


AccountKind = Literal["checking", "savings", "cash", "credit", "loan", "line_of_credit"]


_CASH_ASSET_TYPES = {
    AssetType.CASH,
    AssetType.BANK_ACCOUNT,
    AssetType.BANK_CHECKING,
    AssetType.BANK_SAVINGS,
}


_LIABILITY_KIND_MAP: dict[str, AccountKind] = {
    "credit_card": "credit",
    "line_of_credit": "line_of_credit",
    "mortgage": "loan",
    "car_loan": "loan",
    "personal_loan": "loan",
    "student_loan": "loan",
    "other": "loan",
}


_ASSET_KIND_MAP: dict[AssetType, AccountKind] = {
    AssetType.BANK_CHECKING: "checking",
    AssetType.BANK_SAVINGS: "savings",
    AssetType.BANK_ACCOUNT: "checking",
    AssetType.CASH: "cash",
}


_CASH_KINDS: tuple[AccountKind, ...] = ("checking", "savings", "cash")
_DEBT_KINDS: tuple[AccountKind, ...] = ("credit", "loan", "line_of_credit")


class AccountResponse(BaseModel):
    """A single bank / credit / loan account shown on the Accounts page."""

    id: str  # "asset:42" or "liability:7" so the frontend has a stable key
    name: str
    kind: AccountKind
    balance: float  # Positive for assets, positive for liabilities (amount owed)
    currency: str
    institution: Optional[str] = None
    external_account_id: Optional[str] = None
    last4: Optional[str] = None
    source: Optional[str] = None  # e.g. "wealthsimple"
    updated_at: Optional[datetime] = None


class CurrencyTotals(BaseModel):
    """Cash / debt / net triple for a single currency bucket."""

    cash: float
    debt: float
    net: float


class CombinedTotals(BaseModel):
    """Cross-currency roll-up expressed in a single target currency."""

    cash: float
    debt: float
    net: float
    currency: str


class FxInfo(BaseModel):
    """USD/CAD rate metadata used for combined conversion."""

    usd_cad_rate: Optional[float]
    as_of_date: Optional[str]  # ISO date string
    source: Optional[str]
    is_stale: bool


class AccountsSummary(BaseModel):
    """Roll-up totals for the Accounts page header (legacy CAD-native shape)."""

    total_cash: float
    total_debt: float
    net_cash: float  # cash - debt
    currency: str = "CAD"


class AccountsResponse(BaseModel):
    summary: AccountsSummary
    accounts: list[AccountResponse]
    totals_by_currency: dict[str, CurrencyTotals]
    totals_combined: dict[str, CombinedTotals]
    fx: FxInfo


def _asset_to_account(
    asset: Asset,
    latest_balance: Optional[Decimal] = None,
    latest_balance_date: Optional[datetime] = None,
) -> AccountResponse:
    # Prefer ``AccountBalanceHistory`` (that's where the Wealthsimple
    # importer writes cash sub-balances). Fall back to
    # ``asset.current_price`` for manually-managed assets, which is
    # the old behaviour.
    # Wise API assets: balance lives on ``current_price`` only; ignore snapshot history
    # so Monarch/CSV rows cannot override with $0.
    if latest_balance is not None and not asset.is_wise_api_asset:
        balance = float(latest_balance)
        updated_at = latest_balance_date or asset.price_updated_at
    else:
        balance = float(asset.current_price or Decimal("0"))
        updated_at = asset.price_updated_at
    return AccountResponse(
        id=f"asset:{asset.id}",
        name=asset.name,
        kind=_ASSET_KIND_MAP.get(asset.asset_type, "cash"),
        balance=balance,
        currency=(asset.currency or "CAD").upper(),
        institution=asset.institution,
        external_account_id=asset.external_account_id,
        source=asset.sync_source,
        updated_at=updated_at,
    )


def _latest_balances_by_asset(
    db, asset_ids: list[int]
) -> dict[int, tuple[Decimal, datetime]]:
    """Return ``{asset_id: (balance, as_of_date)}`` for the latest row.

    We pick the most recent ``AccountBalanceHistory`` row where the row
    currency matches the asset's own currency — that's the "native"
    balance the Accounts page cares about. USD sub-balances on a CAD
    retirement account feed the Holdings / Combined views, not the
    Accounts list.
    """
    if not asset_ids:
        return {}
    rows = db.execute(
        select(
            AccountBalanceHistory.asset_id,
            AccountBalanceHistory.balance,
            AccountBalanceHistory.as_of_date,
            AccountBalanceHistory.currency,
            Asset.currency.label("asset_currency"),
        )
        .join(Asset, Asset.id == AccountBalanceHistory.asset_id)
        .where(AccountBalanceHistory.asset_id.in_(asset_ids))
        .order_by(
            AccountBalanceHistory.asset_id.asc(),
            desc(AccountBalanceHistory.as_of_date),
        )
    ).all()

    latest: dict[int, tuple[Decimal, datetime]] = {}
    for asset_id, balance, as_of_date, row_ccy, asset_ccy in rows:
        if asset_id in latest:
            continue  # Already took the most-recent row for this asset.
        if (row_ccy or "").upper() != (asset_ccy or "").upper():
            continue  # Skip cross-currency sub-balances for the native view.
        latest[asset_id] = (balance, as_of_date)
    return latest


def _liability_to_account(liab: Liability) -> AccountResponse:
    kind: AccountKind = _LIABILITY_KIND_MAP.get(liab.liability_type, "loan")
    return AccountResponse(
        id=f"liability:{liab.id}",
        name=liab.name,
        kind=kind,
        balance=float(liab.current_balance or Decimal("0")),
        currency=(liab.currency or "CAD").upper(),
        institution=liab.institution,
        external_account_id=None,
        last4=liab.account_number_last4,
        source=None,
        updated_at=liab.balance_updated_at,
    )


def _roll_up_by_currency(accounts: list[AccountResponse]) -> dict[str, CurrencyTotals]:
    """Sum cash / debt per native currency.

    Always returns at least ``CAD`` and ``USD`` entries (zero-filled) so
    the frontend never needs to handle missing keys.
    """
    buckets: dict[str, dict[str, float]] = {
        "CAD": {"cash": 0.0, "debt": 0.0},
        "USD": {"cash": 0.0, "debt": 0.0},
    }
    for acc in accounts:
        bucket = buckets.setdefault(acc.currency, {"cash": 0.0, "debt": 0.0})
        if acc.kind in _CASH_KINDS:
            bucket["cash"] += acc.balance
        elif acc.kind in _DEBT_KINDS:
            bucket["debt"] += acc.balance
    return {
        ccy: CurrencyTotals(
            cash=vals["cash"],
            debt=vals["debt"],
            net=vals["cash"] - vals["debt"],
        )
        for ccy, vals in buckets.items()
    }


def _combine_totals(
    per_ccy: dict[str, CurrencyTotals],
    usd_cad_rate: Optional[Decimal],
) -> dict[str, CombinedTotals]:
    """Convert per-currency buckets into Combined CAD and Combined USD.

    When ``usd_cad_rate`` is missing (no BoC row yet), use
    ``DISPLAY_FALLBACK_USDCAD`` so combined totals are not all zeros; the
    API still marks FX metadata stale when a fallback was used.
    """
    cad_bucket = per_ccy.get("CAD") or CurrencyTotals(cash=0.0, debt=0.0, net=0.0)
    usd_bucket = per_ccy.get("USD") or CurrencyTotals(cash=0.0, debt=0.0, net=0.0)

    effective = (
        usd_cad_rate
        if usd_cad_rate is not None and usd_cad_rate != 0
        else DISPLAY_FALLBACK_USDCAD
    )
    rate_f = float(effective)

    # USD -> CAD multiplies; CAD -> USD divides.
    usd_in_cad_cash = usd_bucket.cash * rate_f
    usd_in_cad_debt = usd_bucket.debt * rate_f
    cad_in_usd_cash = cad_bucket.cash / rate_f
    cad_in_usd_debt = cad_bucket.debt / rate_f

    combined_cad_cash = cad_bucket.cash + usd_in_cad_cash
    combined_cad_debt = cad_bucket.debt + usd_in_cad_debt
    combined_usd_cash = usd_bucket.cash + cad_in_usd_cash
    combined_usd_debt = usd_bucket.debt + cad_in_usd_debt

    return {
        "CAD": CombinedTotals(
            cash=combined_cad_cash,
            debt=combined_cad_debt,
            net=combined_cad_cash - combined_cad_debt,
            currency="CAD",
        ),
        "USD": CombinedTotals(
            cash=combined_usd_cash,
            debt=combined_usd_debt,
            net=combined_usd_cash - combined_usd_debt,
            currency="USD",
        ),
    }


@router.get("/", response_model=AccountsResponse)
async def list_accounts(db: DbSession) -> AccountsResponse:
    """Return every bank / credit / loan account known to the app."""
    cash_assets = (
        db.execute(
            select(Asset)
            .where(Asset.is_liability.is_(False))
            .where(Asset.asset_type.in_(_CASH_ASSET_TYPES))
        )
        .scalars()
        .all()
    )

    # Pre-fetch the latest balance per cash asset so the Accounts page
    # reflects the real ``AccountBalanceHistory`` value rather than the
    # (almost always empty) ``Asset.current_price`` column.
    latest_balances = _latest_balances_by_asset(
        db, [a.id for a in cash_assets]
    )

    liabilities = (
        db.execute(select(Liability).where(Liability.status == "active"))
        .scalars()
        .all()
    )

    accounts: list[AccountResponse] = [
        *(
            _asset_to_account(
                a,
                latest_balance=(lb := latest_balances.get(a.id)) and lb[0],
                latest_balance_date=lb[1] if lb else None,
            )
            for a in cash_assets
        ),
        *(_liability_to_account(liab) for liab in liabilities),
    ]
    accounts.sort(key=lambda a: (a.institution or "", a.name))

    # Warm the FX cache (no-op when today's rate is already cached) so
    # first-load combined totals aren't forced to wait on a later page
    # hit to populate the rate.
    latest_rate = fx_service.ensure_latest_rate_cached(db)
    db.commit()
    rate_value = latest_rate.rate if latest_rate is not None else None
    used_rate_fallback = rate_value is None

    totals_by_currency = _roll_up_by_currency(accounts)
    totals_combined = _combine_totals(totals_by_currency, rate_value)

    cad_bucket = totals_by_currency["CAD"]
    summary = AccountsSummary(
        total_cash=cad_bucket.cash,
        total_debt=cad_bucket.debt,
        net_cash=cad_bucket.net,
    )

    display_rate = rate_value if rate_value is not None else DISPLAY_FALLBACK_USDCAD
    fx_info = FxInfo(
        usd_cad_rate=float(display_rate),
        as_of_date=(
            latest_rate.as_of_date.isoformat() if latest_rate is not None else None
        ),
        source=(
            "display_fallback_usdcad"
            if used_rate_fallback
            else (latest_rate.source if latest_rate is not None else None)
        ),
        is_stale=used_rate_fallback
        or (fx_service.is_stale(latest_rate) if latest_rate is not None else True),
    )

    return AccountsResponse(
        summary=summary,
        accounts=accounts,
        totals_by_currency=totals_by_currency,
        totals_combined=totals_combined,
        fx=fx_info,
    )
