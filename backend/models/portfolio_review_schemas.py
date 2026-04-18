"""Pydantic schemas for the CAD-only Canadian portfolio review API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class PortfolioReviewLineResponse(BaseModel):
    id: int
    sort_order: int
    investment: str
    platform: str
    value_cad: Optional[Decimal] = None
    pct_global: Optional[Decimal] = None
    return_pct: Optional[Decimal] = None
    div_per_year: Optional[Decimal] = None
    yield_pct: Optional[Decimal] = None
    target_pct: Optional[str] = None
    delta: Optional[str] = None
    conviction: Optional[int] = None
    action: Optional[str] = None
    raw_row: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class PortfolioReviewSummary(BaseModel):
    id: int
    as_of_date: date
    label: Optional[str] = None
    source: str
    total_value_cad: Optional[Decimal] = None
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
    total_value_cad: Optional[Decimal] = None


class CompareResponse(BaseModel):
    from_review: PortfolioReviewSummary
    to_review: PortfolioReviewSummary
    total_cad_delta: Optional[Decimal] = None
    pct_change: Optional[float] = None


class ImportPreviewResponse(BaseModel):
    as_of_date: date
    label: Optional[str] = None
    line_count: int
    total_value_cad: Decimal
    sample_lines: list[dict[str, Any]] = Field(
        default_factory=list,
        description="First rows for UI preview",
    )
