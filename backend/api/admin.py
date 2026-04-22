"""Admin API endpoints (destructive maintenance operations).

Endpoints:

- ``POST /v1/admin/reset-data`` — delete every row from every data table.
  Schema is preserved; this is equivalent to a fresh install for your data
  but leaves Alembic migrations and the users table (if any) in place.
- ``GET /v1/admin/row-counts`` — cheap per-table row count, useful for the
  Settings "danger zone" confirmation screen.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from backend.db.models import (
    AccountBalanceHistory,
    Asset,
    Dividend,
    ImportedEvent,
    Liability,
    LiabilityBalanceHistory,
    LiabilityPayment,
    Lot,
    PortfolioReview,
    PortfolioReviewLine,
    PortfolioSnapshot,
    PriceHistory,
    RealEstatePayment,
    RealEstatePaymentSeries,
    RealEstateProperty,
    SnapshotHolding,
    Transaction,
)
from backend.db.session import DbSession
from backend.services.admin import reset_all_data

router = APIRouter(prefix="/v1/admin", tags=["admin"])


# Required confirmation string. Clients MUST send this literal in the
# ``X-Confirm-Reset`` header to prove the operator knows what they're doing.
CONFIRM_PHRASE = "RESET ALL DATA"


class RowCountsResponse(BaseModel):
    counts: dict[str, int]
    total: int


class ResetResponse(BaseModel):
    deleted: dict[str, int]
    total: int


_COUNT_MODELS = [
    ("assets", Asset),
    ("liabilities", Liability),
    ("transactions", Transaction),
    ("lots", Lot),
    ("dividends", Dividend),
    ("portfolio_snapshots", PortfolioSnapshot),
    ("snapshot_holdings", SnapshotHolding),
    ("portfolio_reviews", PortfolioReview),
    ("portfolio_review_lines", PortfolioReviewLine),
    ("account_balance_history", AccountBalanceHistory),
    ("liability_balance_history", LiabilityBalanceHistory),
    ("liability_payments", LiabilityPayment),
    ("real_estate_properties", RealEstateProperty),
    ("real_estate_payment_series", RealEstatePaymentSeries),
    ("real_estate_payments", RealEstatePayment),
    ("imported_events", ImportedEvent),
    ("price_history", PriceHistory),
]


def _count_rows(db: DbSession, model: type) -> int:
    """COUNT(*) without ORM entity load — avoids errors when the DB lags models (missing columns)."""
    stmt = select(func.count()).select_from(model.__table__)
    return int(db.execute(stmt).scalar_one())


@router.get("/row-counts", response_model=RowCountsResponse)
def row_counts(db: DbSession) -> RowCountsResponse:
    """Return a row count per table for the Settings danger-zone UI."""
    counts = {label: _count_rows(db, model) for label, model in _COUNT_MODELS}
    return RowCountsResponse(counts=counts, total=sum(counts.values()))


@router.post("/reset-data", response_model=ResetResponse)
def reset_data(
    db: DbSession,
    x_confirm_reset: str = Header(..., alias="X-Confirm-Reset"),
) -> ResetResponse:
    """Delete every row from every data table.

    The caller MUST send ``X-Confirm-Reset: RESET ALL DATA`` exactly. Any
    other value (or a missing header) returns 400 without touching the DB.
    """
    if x_confirm_reset != CONFIRM_PHRASE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Missing or incorrect confirmation. "
                f"Send header X-Confirm-Reset: {CONFIRM_PHRASE!r}."
            ),
        )

    report = reset_all_data(db)
    db.commit()
    return ResetResponse(deleted=report.deleted, total=report.total)
