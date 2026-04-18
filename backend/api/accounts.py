"""Accounts API — cash + credit card + line of credit.

Reads directly from the tables populated by the Wealthsimple (and future RBC)
CSV importers so the Accounts page is always in sync with what was imported.

Investments live on the Portfolio / Holdings pages and are intentionally not
returned here. This endpoint is for "money you spend from" (bank accounts)
and "money you owe" (credit cards, LOC, loans).
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability
from backend.db.session import DbSession

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


class AccountsSummary(BaseModel):
    """Roll-up totals for the Accounts page header."""

    total_cash: float
    total_debt: float
    net_cash: float  # cash - debt
    currency: str = "CAD"


class AccountsResponse(BaseModel):
    summary: AccountsSummary
    accounts: list[AccountResponse]


def _asset_to_account(asset: Asset) -> AccountResponse:
    balance = float(asset.current_price or Decimal("0"))
    return AccountResponse(
        id=f"asset:{asset.id}",
        name=asset.name,
        kind=_ASSET_KIND_MAP.get(asset.asset_type, "cash"),
        balance=balance,
        currency=asset.currency or "CAD",
        institution=asset.institution,
        external_account_id=asset.external_account_id,
        source=asset.sync_source,
        updated_at=asset.price_updated_at,
    )


def _liability_to_account(liab: Liability) -> AccountResponse:
    kind: AccountKind = _LIABILITY_KIND_MAP.get(liab.liability_type, "loan")
    return AccountResponse(
        id=f"liability:{liab.id}",
        name=liab.name,
        kind=kind,
        balance=float(liab.current_balance or Decimal("0")),
        currency=liab.currency or "CAD",
        institution=liab.institution,
        external_account_id=None,
        last4=liab.account_number_last4,
        source=None,
        updated_at=liab.balance_updated_at,
    )


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

    liabilities = (
        db.execute(select(Liability).where(Liability.status == "active"))
        .scalars()
        .all()
    )

    accounts: list[AccountResponse] = [
        *(_asset_to_account(a) for a in cash_assets),
        *(_liability_to_account(liab) for liab in liabilities),
    ]
    accounts.sort(key=lambda a: (a.institution or "", a.name))

    total_cash = sum(a.balance for a in accounts if a.kind in ("checking", "savings", "cash"))
    total_debt = sum(
        a.balance for a in accounts if a.kind in ("credit", "loan", "line_of_credit")
    )

    return AccountsResponse(
        summary=AccountsSummary(
            total_cash=total_cash,
            total_debt=total_debt,
            net_cash=total_cash - total_debt,
        ),
        accounts=accounts,
    )
