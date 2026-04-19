"""FX rate API — read-only endpoints for the Questrade-style view toggle.

The frontend fetches the current USD/CAD rate on mount and whenever the
user flips the currency view. The endpoint is intentionally cheap: it
hits the cached ``fx_rates`` table, lazily warms today's rate from
Bank of Canada if it's stale, and returns the result with a ``is_stale``
flag so the UI can display a banner if we're unable to refresh.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.session import DbSession
from backend.services import fx as fx_service

router = APIRouter(prefix="/v1/fx", tags=["fx"])


class UsdCadRateResponse(BaseModel):
    """Current USD/CAD closing rate plus metadata for the UI banner."""

    pair: str = "USDCAD"
    rate: Optional[float]
    as_of_date: Optional[date]
    source: Optional[str]
    is_stale: bool


@router.get("/usd-cad", response_model=UsdCadRateResponse)
def get_usd_cad_rate(db: DbSession) -> UsdCadRateResponse:
    """Return the latest USD/CAD rate, warming from BoC if it's stale.

    This endpoint is safe to call on every page load; the fetch is a
    no-op when today's rate is already cached.
    """
    latest = fx_service.ensure_latest_rate_cached(db)
    # ``ensure_latest_rate_cached`` may commit a new row; persist it so
    # the rest of the request sees it even if nothing else touches the
    # session.
    db.commit()
    if latest is None:
        return UsdCadRateResponse(
            rate=None,
            as_of_date=None,
            source=None,
            is_stale=True,
        )
    return UsdCadRateResponse(
        rate=float(latest.rate),
        as_of_date=latest.as_of_date,
        source=latest.source,
        is_stale=fx_service.is_stale(latest),
    )


class BackfillRequest(BaseModel):
    """Inputs for a one-shot historical FX backfill."""

    # Defaulting to a year of history keeps the most common
    # net-worth-timeline use case covered without a huge payload.
    days: int = 365


class BackfillResponse(BaseModel):
    """Summary of how many rows were fetched."""

    observations_written: int
    start_date: date
    end_date: date


@router.post("/backfill", response_model=BackfillResponse)
def backfill_usd_cad(payload: BackfillRequest, db: DbSession) -> BackfillResponse:
    """Fetch the last ``days`` of BoC USD/CAD observations and UPSERT."""
    end = date.today()
    start = end - timedelta(days=max(1, payload.days))
    written = fx_service.backfill_rates(db, start_date=start, end_date=end)
    db.commit()
    return BackfillResponse(
        observations_written=written, start_date=start, end_date=end
    )
