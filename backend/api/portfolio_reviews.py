"""Semi-annual portfolio review API: CSV import, allocation, timeline, compare."""

from collections import defaultdict
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.db.models.portfolio_review import (
    PortfolioReview,
    PortfolioReviewLine,
    ReviewSource,
)
from backend.db.session import DbSession
from backend.models.portfolio_review_schemas import (
    AllocationResponse,
    AllocationSlice,
    CompareResponse,
    ImportPreviewResponse,
    PortfolioReviewDetail,
    PortfolioReviewLineResponse,
    PortfolioReviewSummary,
    RegionDelta,
    TimelinePoint,
)
from backend.services.portfolio_review_parser import (
    ParsedLine,
    parse_portfolio_review_text,
    total_usd,
)

router = APIRouter(prefix="/v1/portfolio-reviews", tags=["portfolio-reviews"])

GroupBy = Literal["region", "platform", "conviction"]


def _review_to_summary(r: PortfolioReview) -> PortfolioReviewSummary:
    return PortfolioReviewSummary.model_validate(r)


def _line_to_response(ln: PortfolioReviewLine) -> PortfolioReviewLineResponse:
    return PortfolioReviewLineResponse.model_validate(ln)


def _parsed_line_to_db(
    pl: ParsedLine, review_id: int, sort_order: int
) -> PortfolioReviewLine:
    raw = pl.raw if isinstance(pl.raw, dict) else {}
    return PortfolioReviewLine(
        review_id=review_id,
        sort_order=sort_order,
        region=pl.region,
        investment=pl.investment,
        platform=pl.platform,
        currency=pl.currency,
        value_native=pl.value_native,
        value_usd=pl.value_usd,
        pct_region=pl.pct_region,
        pct_global=pl.pct_global,
        return_pct=pl.return_pct,
        div_per_year=pl.div_per_year,
        yield_pct=pl.yield_pct,
        fx_note=pl.fx_note,
        target_pct=pl.target_pct,
        delta=pl.delta,
        conviction=pl.conviction,
        action=pl.action,
        raw_row=raw,
    )


@router.get("/", response_model=list[PortfolioReviewSummary])
async def list_reviews(
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
):
    rows = db.execute(
        select(PortfolioReview).order_by(PortfolioReview.as_of_date.desc()).limit(limit)
    ).scalars().all()
    return [_review_to_summary(r) for r in rows]


@router.get("/timeline", response_model=list[TimelinePoint])
async def timeline(db: DbSession):
    rows = db.execute(
        select(PortfolioReview).order_by(PortfolioReview.as_of_date.asc())
    ).scalars().all()
    return [
        TimelinePoint(
            id=r.id,
            as_of_date=r.as_of_date,
            total_value_usd=r.total_value_usd,
        )
        for r in rows
    ]


@router.get("/compare", response_model=CompareResponse)
async def compare_reviews(
    db: DbSession,
    from_id: int = Query(..., description="Earlier review id"),
    to_id: int = Query(..., description="Later review id"),
):
    a = db.execute(
        select(PortfolioReview).where(PortfolioReview.id == from_id)
    ).scalar_one_or_none()
    b = db.execute(
        select(PortfolioReview).where(PortfolioReview.id == to_id)
    ).scalar_one_or_none()
    if not a or not b:
        raise HTTPException(status_code=404, detail="Review not found")

    ta = a.total_value_usd
    tb = b.total_value_usd
    delta: Optional[Decimal] = None
    pct: Optional[float] = None
    if ta is not None and tb is not None:
        delta = tb - ta
        if ta != 0:
            pct = float((tb - ta) / ta * 100)

    lines_a = db.execute(
        select(PortfolioReviewLine).where(PortfolioReviewLine.review_id == from_id)
    ).scalars().all()
    lines_b = db.execute(
        select(PortfolioReviewLine).where(PortfolioReviewLine.review_id == to_id)
    ).scalars().all()

    def by_region(lines: list[PortfolioReviewLine]) -> dict[str, Decimal]:
        m: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for ln in lines:
            m[ln.region] += ln.value_usd or Decimal("0")
        return dict(m)

    ra, rb = by_region(lines_a), by_region(lines_b)
    regions = sorted(set(ra) | set(rb))
    region_deltas: list[RegionDelta] = []
    for reg in regions:
        fa = ra.get(reg, Decimal("0"))
        fb = rb.get(reg, Decimal("0"))
        region_deltas.append(
            RegionDelta(region=reg, from_usd=fa, to_usd=fb, delta_usd=fb - fa)
        )

    return CompareResponse(
        from_review=_review_to_summary(a),
        to_review=_review_to_summary(b),
        total_usd_delta=delta,
        pct_change=pct,
        region_deltas=region_deltas,
    )


@router.get("/{review_id}", response_model=PortfolioReviewDetail)
async def get_review(review_id: int, db: DbSession):
    r = db.execute(
        select(PortfolioReview)
        .options(selectinload(PortfolioReview.lines))
        .where(PortfolioReview.id == review_id)
    ).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    lines = sorted(r.lines, key=lambda x: x.sort_order)
    return PortfolioReviewDetail(
        **_review_to_summary(r).model_dump(),
        lines=[_line_to_response(ln) for ln in lines],
    )


@router.delete("/{review_id}")
async def delete_review(review_id: int, db: DbSession):
    r = db.execute(
        select(PortfolioReview).where(PortfolioReview.id == review_id)
    ).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(r)
    db.commit()
    return {"ok": True, "deleted_id": review_id}


@router.get("/{review_id}/allocation", response_model=AllocationResponse)
async def get_allocation(
    review_id: int,
    db: DbSession,
    group_by: GroupBy = Query("region"),
):
    r = db.execute(
        select(PortfolioReview).where(PortfolioReview.id == review_id)
    ).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")

    lines = db.execute(
        select(PortfolioReviewLine).where(PortfolioReviewLine.review_id == review_id)
    ).scalars().all()

    buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for ln in lines:
        vu = ln.value_usd or Decimal("0")
        if group_by == "region":
            key = ln.region
        elif group_by == "platform":
            p = (ln.platform or "").strip()
            key = p if p else "(none)"
        else:
            key = str(ln.conviction) if ln.conviction is not None else "unset"
        buckets[key] += vu

    total = sum(buckets.values(), start=Decimal("0"))
    denom = total if total != 0 else Decimal("1")
    slices: list[AllocationSlice] = []
    for key in sorted(buckets.keys()):
        v = buckets[key]
        slices.append(
            AllocationSlice(
                key=key,
                value_usd=v,
                pct=float(v / denom * 100),
            )
        )

    return AllocationResponse(
        review_id=review_id,
        group_by=group_by,
        total_usd=total,
        slices=slices,
    )


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_import(file: UploadFile = File(...)):
    try:
        raw = await file.read()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid encoding: {e}") from e

    parsed = parse_portfolio_review_text(text)
    t = total_usd(parsed.lines)
    sample: list[dict[str, str | None]] = []
    for pl in parsed.lines[:25]:
        sample.append(
            {
                "region": pl.region,
                "investment": pl.investment,
                "platform": pl.platform,
                "value_usd": str(pl.value_usd) if pl.value_usd is not None else None,
            }
        )
    return ImportPreviewResponse(
        as_of_date=parsed.as_of_date,
        label=parsed.label,
        line_count=len(parsed.lines),
        total_value_usd=t,
        sample_lines=sample,
    )


@router.post("/import", response_model=PortfolioReviewDetail)
async def import_review(
    db: DbSession,
    file: UploadFile = File(...),
    label: Optional[str] = Query(None, max_length=64),
    replace: bool = Query(
        False,
        description="If true, replace existing review with the same as_of_date",
    ),
):
    try:
        raw = await file.read()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid encoding: {e}") from e

    parsed = parse_portfolio_review_text(text)
    if not parsed.lines:
        raise HTTPException(
            status_code=400,
            detail=(
                "No data rows found. Check section headers "
                "(Brazil / Canada / Crypto) and value columns."
            ),
        )

    eff_label = label if label is not None else parsed.label

    existing = db.execute(
        select(PortfolioReview).where(
            PortfolioReview.as_of_date == parsed.as_of_date
        )
    ).scalar_one_or_none()

    if existing and not replace:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A review already exists for {parsed.as_of_date}. "
                "Pass replace=true to overwrite."
            ),
        )

    if existing and replace:
        db.delete(existing)
        db.flush()

    tot = total_usd(parsed.lines)
    pr = PortfolioReview(
        as_of_date=parsed.as_of_date,
        label=eff_label,
        source=ReviewSource.CSV_IMPORT.value,
        total_value_usd=tot,
    )
    db.add(pr)
    db.flush()

    for i, pl in enumerate(parsed.lines):
        db.add(_parsed_line_to_db(pl, pr.id, i))

    db.commit()
    db.refresh(pr)

    r = db.execute(
        select(PortfolioReview)
        .options(selectinload(PortfolioReview.lines))
        .where(PortfolioReview.id == pr.id)
    ).scalar_one()
    lines = sorted(r.lines, key=lambda x: x.sort_order)
    return PortfolioReviewDetail(
        **_review_to_summary(r).model_dump(),
        lines=[_line_to_response(ln) for ln in lines],
    )
