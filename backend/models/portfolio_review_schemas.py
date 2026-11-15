"""Pydantic schemas for the CAD-only Canadian portfolio review API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class PortfolioReviewLineResponse(BaseModel):
    id: int
    sort_order: int
    investment: str
    platform: str
    value_cad: Decimal | None = None
    pct_global: Decimal | None = None
    return_pct: Decimal | None = None
    div_per_year: Decimal | None = None
    yield_pct: Decimal | None = None
    target_pct: str | None = None
    delta: str | None = None
    conviction: int | None = None
    action: str | None = None
    raw_row: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class PortfolioReviewSummary(BaseModel):
    id: int
    as_of_date: date
    label: str | None = None
    source: str
    total_value_cad: Decimal | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioReviewDetail(PortfolioReviewSummary):
    lines: list[PortfolioReviewLineResponse] = Field(default_factory=list)


class AllocationSlice(BaseModel):
    key: str
    value_cad: Decimal
    pct: float


class AllocationResponse(BaseModel):
    review_id: int
    group_by: str
    total_cad: Decimal
    slices: list[AllocationSlice]


class TimelinePoint(BaseModel):
    id: int
    as_of_date: date
    total_value_cad: Decimal | None = None


class CompareResponse(BaseModel):
    from_review: PortfolioReviewSummary
    to_review: PortfolioReviewSummary
    total_cad_delta: Decimal | None = None
    pct_change: float | None = None


class ImportPreviewResponse(BaseModel):
    as_of_date: date
    label: str | None = None
    line_count: int
    total_value_cad: Decimal
    sample_lines: list[dict[str, Any]] = Field(
        default_factory=list,
        description="First rows for UI preview",
    )


class BatchImportFileResult(BaseModel):
    """Result for one file in a multi-file portfolio-review import."""

    filename: str
    success: bool
    review_id: int | None = None
    as_of_date: date | None = None
    line_count: int | None = None
    total_value_cad: Decimal | None = None
    error: str | None = None


class BatchImportResponse(BaseModel):
    results: list[BatchImportFileResult]
    imported_count: int
    failed_count: int
