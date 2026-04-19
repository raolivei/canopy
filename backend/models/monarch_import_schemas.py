"""Pydantic schemas for Monarch Money CSV import endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MonarchFileReport(BaseModel):
    filename: str
    header_ok: bool
    rows_seen: int
    imported: int
    skipped_pseudo: int
    skipped_foreign: int
    skipped_unknown_account: int
    skipped_ws_covered: int
    skipped_canonical_dup: int
    skipped_source_dup: int
    assets_created: list[str] = Field(default_factory=list)
    liabilities_created: list[str] = Field(default_factory=list)
    assets_touched: list[str] = Field(default_factory=list)
    liabilities_touched: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MonarchPreviewResponse(BaseModel):
    files: list[MonarchFileReport]
    would_import: int
    assets_would_create: list[str] = Field(default_factory=list)
    liabilities_would_create: list[str] = Field(default_factory=list)


class MonarchCommitResponse(BaseModel):
    files: list[MonarchFileReport]
    transactions_added: int
    assets_created: list[str] = Field(default_factory=list)
    liabilities_created: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Balances import (Monarch "Download account balances" CSV)
# ---------------------------------------------------------------------------


class MonarchBalancesFileReport(BaseModel):
    filename: str
    header_ok: bool
    rows_seen: int
    inserted: int
    updated: int
    skipped_pseudo: int
    skipped_foreign: int
    skipped_unknown_account: int
    assets_created: list[str] = Field(default_factory=list)
    liabilities_created: list[str] = Field(default_factory=list)
    assets_touched: list[str] = Field(default_factory=list)
    liabilities_touched: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MonarchBalancesPreviewResponse(BaseModel):
    files: list[MonarchBalancesFileReport]
    would_insert: int
    would_update: int
    assets_would_create: list[str] = Field(default_factory=list)
    liabilities_would_create: list[str] = Field(default_factory=list)


class MonarchBalancesCommitResponse(BaseModel):
    files: list[MonarchBalancesFileReport]
    balances_inserted: int
    balances_updated: int
    assets_created: list[str] = Field(default_factory=list)
    liabilities_created: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Unified endpoints (mixed transactions + balances CSVs in one drop)
# ---------------------------------------------------------------------------


class MonarchMixedPreviewResponse(BaseModel):
    transactions: MonarchPreviewResponse
    balances: MonarchBalancesPreviewResponse


class MonarchMixedCommitResponse(BaseModel):
    transactions: MonarchCommitResponse
    balances: MonarchBalancesCommitResponse
