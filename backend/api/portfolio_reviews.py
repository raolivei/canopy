"""Canadian portfolio review API: CSV import, allocation, timeline, compare.

All values are CAD. Legacy Brazil / Crypto sections in imported CSVs are
ignored by the parser; only the Canada section contributes.
"""

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
    BatchImportFileResult,
    BatchImportResponse,
    CompareResponse,
    ImportPreviewResponse,
    PortfolioReviewDetail,
    PortfolioReviewLineResponse,
    PortfolioReviewSummary,
    TimelinePoint,
)
from backend.services.portfolio_review_parser import (
    ParsedLine,
    parse_portfolio_review_text,
    total_cad,
)

router = APIRouter(prefix="/v1/portfolio-reviews", tags=["portfolio-reviews"])

GroupBy = Literal["platform", "conviction"]


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
        investment=pl.investment,
        platform=pl.platform,
        value_cad=pl.value_cad,
        pct_global=pl.pct_global,
        return_pct=pl.return_pct,
        div_per_year=pl.div_per_year,
        yield_pct=pl.yield_pct,
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
    rows = (
        db.execute(
            select(PortfolioReview)
            .order_by(PortfolioReview.as_of_date.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_review_to_summary(r) for r in rows]


@router.get("/timeline", response_model=list[TimelinePoint])
async def timeline(db: DbSession):
    rows = (
        db.execute(
            select(PortfolioReview).order_by(PortfolioReview.as_of_date.asc())
        )
        .scalars()
        .all()
    )
    return [
        TimelinePoint(
            id=r.id,
            as_of_date=r.as_of_date,
            total_value_cad=r.total_value_cad,
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

    ta = a.total_value_cad
    tb = b.total_value_cad
    delta: Optional[Decimal] = None
    pct: Optional[float] = None
    if ta is not None and tb is not None:
        delta = tb - ta
        if ta != 0:
            pct = float((tb - ta) / ta * 100)

    return CompareResponse(
        from_review=_review_to_summary(a),
        to_review=_review_to_summary(b),
        total_cad_delta=delta,
        pct_change=pct,
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
    group_by: GroupBy = Query("platform"),
):
    r = db.execute(
        select(PortfolioReview).where(PortfolioReview.id == review_id)
    ).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")

    lines = (
        db.execute(
            select(PortfolioReviewLine).where(
                PortfolioReviewLine.review_id == review_id
            )
        )
        .scalars()
        .all()
    )

    buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for ln in lines:
        v = ln.value_cad or Decimal("0")
        if group_by == "platform":
            p = (ln.platform or "").strip()
            key = p if p else "(none)"
        else:
            key = str(ln.conviction) if ln.conviction is not None else "unset"
        buckets[key] += v

    total = sum(buckets.values(), start=Decimal("0"))
    denom = total if total != 0 else Decimal("1")
    slices: list[AllocationSlice] = [
        AllocationSlice(
            key=key,
            value_cad=buckets[key],
            pct=float(buckets[key] / denom * 100),
        )
        for key in sorted(buckets.keys())
    ]

    return AllocationResponse(
        review_id=review_id,
        group_by=group_by,
        total_cad=total,
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
    t = total_cad(parsed.lines)
    sample: list[dict[str, str | None]] = []
    for pl in parsed.lines[:25]:
        sample.append(
            {
                "investment": pl.investment,
                "platform": pl.platform,
                "value_cad": str(pl.value_cad) if pl.value_cad is not None else None,
            }
        )
    return ImportPreviewResponse(
        as_of_date=parsed.as_of_date,
        label=parsed.label,
        line_count=len(parsed.lines),
        total_value_cad=t,
        sample_lines=sample,
    )


def _import_one(
    db,
    raw_bytes: bytes,
    *,
    label: Optional[str],
    replace: bool,
) -> PortfolioReview:
    """Persist a single portfolio-review CSV. Raises HTTPException on any error."""
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid encoding: {e}") from e

    parsed = parse_portfolio_review_text(text)
    if not parsed.lines:
        raise HTTPException(
            status_code=400,
            detail=(
                "No Canadian rows found. Ensure the CSV has a 'Canada Portfolio' "
                "section with a 'Value (CAD)' column."
            ),
        )

    eff_label = label if label is not None else parsed.label

    existing = db.execute(
        select(PortfolioReview).where(PortfolioReview.as_of_date == parsed.as_of_date)
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

    tot = total_cad(parsed.lines)
    pr = PortfolioReview(
        as_of_date=parsed.as_of_date,
        label=eff_label,
        source=ReviewSource.CSV_IMPORT.value,
        total_value_cad=tot,
    )
    db.add(pr)
    db.flush()

    for i, pl in enumerate(parsed.lines):
        db.add(_parsed_line_to_db(pl, pr.id, i))

    db.commit()
    db.refresh(pr)
    return pr


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
    raw = await file.read()
    pr = _import_one(db, raw, label=label, replace=replace)

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


@router.post("/import/batch", response_model=BatchImportResponse)
async def import_reviews_batch(
    db: DbSession,
    files: list[UploadFile] = File(...),
    label: Optional[str] = Query(None, max_length=64),
    replace: bool = Query(
        False,
        description=(
            "If true, replace existing reviews that share an as_of_date with any "
            "incoming file."
        ),
    ),
):
    """Import multiple portfolio-review CSVs in one request.

    Each file is processed in its own transaction so one failure (bad encoding,
    no Canada section, duplicate as_of_date, etc.) does not kill the others.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results: list[BatchImportFileResult] = []
    for f in files:
        filename = f.filename or "upload.csv"
        try:
            raw = await f.read()
            pr = _import_one(db, raw, label=label, replace=replace)
            results.append(
                BatchImportFileResult(
                    filename=filename,
                    success=True,
                    review_id=pr.id,
                    as_of_date=pr.as_of_date,
                    line_count=len(pr.lines),
                    total_value_cad=pr.total_value_cad,
                )
            )
        except HTTPException as e:
            db.rollback()
            results.append(
                BatchImportFileResult(
                    filename=filename,
                    success=False,
                    error=str(e.detail),
                )
            )
        except Exception as e:
            db.rollback()
            results.append(
                BatchImportFileResult(
                    filename=filename,
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                )
            )

    imported = sum(1 for r in results if r.success)
    return BatchImportResponse(
        results=results,
        imported_count=imported,
        failed_count=len(results) - imported,
    )
