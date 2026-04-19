"""Pydantic request/response schemas for the Wealthsimple CSV importer."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class WsFileClassification(BaseModel):
    filename: str
    account_label: str
    account_kind: str
    account_class: str
    account_number: Optional[str] = None
    statement_period_start: Optional[date] = None
    shape: str
    skipped: bool
    skip_reason: Optional[str] = None
    rows_seen: int = 0
    rows_imported: int = 0
    rows_duplicate: int = 0
    rows_unknown: int = 0
    by_kind: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class WsPreviewResponse(BaseModel):
    files: list[WsFileClassification]
    total_rows_seen: int = 0
    total_would_import: int = 0
    total_duplicates: int = 0


class WsCommitResponse(BaseModel):
    files: list[WsFileClassification]
    assets_touched: list[str]
    liabilities_touched: list[str]
    transactions_added: int
    lots_added: int
    dividends_added: int
    account_snapshots_added: int
    liability_snapshots_added: int
    duplicates_skipped: int


class WsSubBalance(BaseModel):
    """Currency-specific balance for a single Wealthsimple account.

    A CAD TFSA that holds US equities will typically show one CAD
    sub-balance (cash + settlement) and one USD sub-balance (holdings +
    USD cash). We surface both so the frontend can render
    Questrade-style dual balances on each account card.
    """

    currency: str
    balance: Decimal
    as_of_date: Optional[date] = None


class WsAccountSummary(BaseModel):
    kind: str  # "asset" | "liability"
    symbol_or_name: str
    display_name: str
    account_type: str
    institution: str
    currency: str
    # Legacy CAD-native balance, kept for back-compat with older
    # frontends. Mirrors ``balances_by_currency["CAD"]`` when present.
    current_balance: Optional[Decimal] = None
    balance_updated_at: Optional[date] = None
    balances_by_currency: list[WsSubBalance] = []


class NetWorthSlice(BaseModel):
    """One currency slice of a net-worth point.

    ``currency`` is the target unit (CAD, USD). The three headline
    figures follow the same sign convention as :class:`NetWorthPoint`:
    ``debt`` is positive (amount owed), ``net_worth = investments +
    cash - debt``.
    """

    investments: Decimal
    cash: Decimal
    debt: Decimal
    net_worth: Decimal
    currency: str


class NetWorthPoint(BaseModel):
    """A single point on the net-worth timeline.

    The legacy top-level fields (``investments``, ``cash``, ``debt``,
    ``net_worth``) mirror ``cad`` so existing clients continue to work
    without modification. New clients should read the ``cad`` / ``usd``
    / ``combined_cad`` / ``combined_usd`` slices directly based on the
    selected currency view.
    """

    date: date
    investments: Decimal
    cash: Decimal
    debt: Decimal
    net_worth: Decimal
    cad: NetWorthSlice
    usd: NetWorthSlice
    combined_cad: NetWorthSlice
    combined_usd: NetWorthSlice
    fx_rate: Optional[Decimal] = None


class NetWorthTimelineResponse(BaseModel):
    points: list[NetWorthPoint]
    latest_investments: Decimal = Decimal("0")
    latest_cash: Decimal = Decimal("0")
    latest_debt: Decimal = Decimal("0")
    latest_net_worth: Decimal = Decimal("0")
    latest_cad: Optional[NetWorthSlice] = None
    latest_usd: Optional[NetWorthSlice] = None
    latest_combined_cad: Optional[NetWorthSlice] = None
    latest_combined_usd: Optional[NetWorthSlice] = None
    fx_rate: Optional[Decimal] = None
    fx_as_of_date: Optional[date] = None
    fx_is_stale: bool = True
