"""Resolve a Monarch account label to a Canopy Asset or Liability.

Monarch account labels look like:

* ``RBC Day to Day Banking (...8813)``
* ``Scotia Momentum VISA Infinite (...5011)``
* ``MANAGED_TFSA (...DqRQ)``
* ``CASH (...1s1h)``
* ``CanadaLife DPSP``  (no trailing last4)

Resolution strategy:

1. **Exact match on an existing Canopy entity's name** - catches
   re-imports and deliberate manual-naming alignment.
2. **Last-4 match** against ``Asset.external_account_id`` or
   ``Liability.account_number_last4`` - catches the common case where a
   Wealthsimple-imported account and a Monarch-imported account refer to
   the same real-world thing via the same trailing identifier.
3. **Autocreate** a new Asset or Liability with conservative defaults.
   The caller gets back the resolved entity plus a flag telling it
   whether an entity was created.

The resolver is intentionally dumb about fuzzy name matching. False
merges would be worse than a duplicate account: the user can always
merge two accounts by hand later, but un-merging a bad match is
painful.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability, LiabilityType
from backend.services.monarch.parser import AccountClass
from sqlalchemy import select
from sqlalchemy.orm import Session

INSTITUTION = "Imported from Monarch"


@dataclass
class ResolvedAccount:
    """Outcome of resolving one Monarch account label."""

    label: str  # original Monarch label
    account_class: AccountClass
    asset: Optional[Asset] = None
    liability: Optional[Liability] = None
    created: bool = False
    note: Optional[str] = None

    @property
    def kind(self) -> str:
        if self.asset is not None:
            return "asset"
        if self.liability is not None:
            return "liability"
        return "none"

    @property
    def canopy_name(self) -> Optional[str]:
        if self.asset is not None:
            return self.asset.name
        if self.liability is not None:
            return self.liability.name
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_account(
    db: Session,
    *,
    label: str,
    account_class: AccountClass,
    last4: Optional[str],
    currency: str = "CAD",
) -> Optional[ResolvedAccount]:
    """Resolve a single Monarch account label.

    Returns ``None`` when the class is ``PSEUDO`` or ``UNKNOWN`` - the
    caller should skip the row. ``currency`` is used only when
    autocreating a new Asset / Liability: existing entities keep their
    stored currency.
    """
    if account_class in {AccountClass.PSEUDO, AccountClass.UNKNOWN, AccountClass.FOREIGN}:
        return None

    if account_class == AccountClass.DEBT:
        return _resolve_liability(db, label=label, last4=last4, currency=currency)

    # INVESTMENT and CASH both land on an Asset row.
    return _resolve_asset(
        db, label=label, account_class=account_class, last4=last4, currency=currency
    )


# ---------------------------------------------------------------------------
# Asset resolution
# ---------------------------------------------------------------------------


def _resolve_asset(
    db: Session,
    *,
    label: str,
    account_class: AccountClass,
    last4: Optional[str],
    currency: str,
) -> ResolvedAccount:
    # 1) name match
    existing = db.execute(select(Asset).where(Asset.name == label)).scalar_one_or_none()
    if existing is not None:
        return ResolvedAccount(label=label, account_class=account_class, asset=existing)

    # 2) last4 match on external_account_id
    if last4:
        existing = db.execute(select(Asset).where(Asset.external_account_id.like(f"%{last4}"))).scalar_one_or_none()
        if existing is not None:
            return ResolvedAccount(
                label=label,
                account_class=account_class,
                asset=existing,
                note=f"matched existing asset '{existing.name}' by last4 '{last4}'",
            )

    # 3) autocreate
    asset = Asset(
        symbol=_unique_symbol(db, label),
        name=label,
        asset_type=_asset_type_for(label, account_class),
        currency=currency if currency in {"CAD", "USD"} else "CAD",
        institution=INSTITUTION,
        country="CA",
        sync_source="csv_import",
        external_account_id=last4,
    )
    db.add(asset)
    db.flush()
    return ResolvedAccount(
        label=label,
        account_class=account_class,
        asset=asset,
        created=True,
        note="autocreated from Monarch import",
    )


def _asset_type_for(label: str, account_class: AccountClass) -> AssetType:
    lower = label.lower()
    if "tfsa" in lower:
        return AssetType.RETIREMENT_TFSA
    if "rrsp" in lower:
        return AssetType.RETIREMENT_RRSP
    if "fhsa" in lower:
        return AssetType.RETIREMENT_FHSA
    if "dpsp" in lower:
        return AssetType.RETIREMENT_DPSP
    if "crypto" in lower:
        return AssetType.CRYPTO
    if "savings" in lower or "find & save" in lower:
        return AssetType.BANK_SAVINGS
    if "chequing" in lower or "checking" in lower or "day to day" in lower or "cad account" in lower:
        return AssetType.BANK_CHECKING
    if account_class == AccountClass.CASH:
        return AssetType.CASH
    return AssetType.OTHER


# ---------------------------------------------------------------------------
# Liability resolution
# ---------------------------------------------------------------------------


def _resolve_liability(
    db: Session,
    *,
    label: str,
    last4: Optional[str],
    currency: str,
) -> ResolvedAccount:
    existing = db.execute(select(Liability).where(Liability.name == label)).scalar_one_or_none()
    if existing is not None:
        return ResolvedAccount(label=label, account_class=AccountClass.DEBT, liability=existing)

    if last4:
        existing = db.execute(
            select(Liability).where(Liability.account_number_last4 == last4[-4:])
        ).scalar_one_or_none()
        if existing is not None:
            return ResolvedAccount(
                label=label,
                account_class=AccountClass.DEBT,
                liability=existing,
                note=f"matched existing liability '{existing.name}' by last4 '{last4[-4:]}'",
            )

    liability_type = _liability_type_for(label)
    liability = Liability(
        name=label,
        institution=INSTITUTION,
        liability_type=liability_type.value,
        account_number_last4=last4[-4:] if last4 else None,
        currency=currency if currency in {"CAD", "USD"} else "CAD",
        country="CA",
    )
    db.add(liability)
    db.flush()
    return ResolvedAccount(
        label=label,
        account_class=AccountClass.DEBT,
        liability=liability,
        created=True,
        note="autocreated from Monarch import",
    )


def _liability_type_for(label: str) -> LiabilityType:
    lower = label.lower()
    # Check credit-card markers *first* — otherwise substrings like "car"
    # inside "Mastercard"/"credit card" would mis-route every CC into a
    # car loan.
    if any(
        kw in lower
        for kw in ("credit card", "credit_card", "mastercard", "visa", "amex", "american express")
    ):
        return LiabilityType.CREDIT_CARD
    if (
        "line of credit" in lower
        or "line_of_credit" in lower
        or "credit line" in lower
        or "loc" in lower
    ):
        return LiabilityType.LINE_OF_CREDIT
    if "mortgage" in lower:
        return LiabilityType.MORTGAGE
    if "car loan" in lower or "auto loan" in lower or lower.startswith(("car ", "auto ")):
        return LiabilityType.CAR_LOAN
    if "student" in lower:
        return LiabilityType.STUDENT_LOAN
    return LiabilityType.CREDIT_CARD


# ---------------------------------------------------------------------------
# Symbol generation (Assets have a unique NOT NULL ``symbol`` column)
# ---------------------------------------------------------------------------


def _unique_symbol(db: Session, label: str) -> str:
    """Generate a stable, unique Asset.symbol from a Monarch label.

    Symbols must be unique across all Assets. We slug the label and
    append a numeric suffix if needed.
    """
    base = _slug(label) or "monarch-account"
    base = f"MONARCH-{base[:40]}"
    candidate = base
    n = 2
    while db.execute(select(Asset.id).where(Asset.symbol == candidate)).scalar_one_or_none() is not None:
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def _slug(label: str) -> str:
    out = []
    for ch in label:
        if ch.isalnum():
            out.append(ch.upper())
        elif ch in (" ", "-", "_"):
            out.append("-")
    return "".join(out).strip("-")
