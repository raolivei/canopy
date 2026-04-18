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


class WsAccountSummary(BaseModel):
    kind: str  # "asset" | "liability"
    symbol_or_name: str
    display_name: str
    account_type: str
    institution: str
    currency: str
    current_balance: Optional[Decimal] = None
    balance_updated_at: Optional[date] = None


class NetWorthPoint(BaseModel):
    date: date
    investments: Decimal
    cash: Decimal
    debt: Decimal
    net_worth: Decimal


class NetWorthTimelineResponse(BaseModel):
    points: list[NetWorthPoint]
    latest_investments: Decimal = Decimal("0")
    latest_cash: Decimal = Decimal("0")
    latest_debt: Decimal = Decimal("0")
    latest_net_worth: Decimal = Decimal("0")
