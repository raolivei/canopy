"""Monarch Money CSV import API.

Endpoints:

* ``POST /v1/monarch-import/preview`` - parse + classify files, return a
  per-file summary without touching the database.
* ``POST /v1/monarch-import/commit`` - parse, classify, and persist to
  the database with per-account Wealthsimple cutover + canonical-hash
  cross-source dedup.

The preview endpoint uses a savepoint so that any autocreated accounts
computed during the dry run are rolled back - users see the same
"assets_created" / "liabilities_created" lists without any side-effects.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.db.session import DbSession
from backend.models.monarch_import_schemas import (
    MonarchCommitResponse,
    MonarchFileReport,
    MonarchPreviewResponse,
)
from backend.services.monarch.importer import FileReport, MonarchImporter

router = APIRouter(prefix="/v1/monarch-import", tags=["monarch-import"])

MAX_FILES = 5
MAX_BYTES = 25 * 1024 * 1024  # 25MB / file - Monarch exports can get large


async def _collect_files(files: list[UploadFile]) -> list[tuple[str, str]]:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Too many files (max {MAX_FILES})")
    collected: list[tuple[str, str]] = []
    for upload in files:
        if not upload.filename:
            continue
        raw = await upload.read()
        if len(raw) > MAX_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"{upload.filename} exceeds {MAX_BYTES} bytes",
            )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"{upload.filename}: not valid UTF-8 ({exc})",
            ) from exc
        collected.append((upload.filename, text))
    return collected


def _report_to_schema(r: FileReport) -> MonarchFileReport:
    return MonarchFileReport(
        filename=r.filename,
        header_ok=r.header_ok,
        rows_seen=r.rows_seen,
        imported=r.imported,
        skipped_pseudo=r.skipped_pseudo,
        skipped_foreign=r.skipped_foreign,
        skipped_unknown_account=r.skipped_unknown_account,
        skipped_ws_covered=r.skipped_ws_covered,
        skipped_canonical_dup=r.skipped_canonical_dup,
        skipped_source_dup=r.skipped_source_dup,
        assets_created=r.assets_created,
        liabilities_created=r.liabilities_created,
        assets_touched=sorted(r.assets_touched),
        liabilities_touched=sorted(r.liabilities_touched),
        warnings=r.warnings,
    )


@router.post("/preview", response_model=MonarchPreviewResponse)
async def preview(
    db: DbSession,
    files: list[UploadFile] = File(...),
) -> MonarchPreviewResponse:
    payload = await _collect_files(files)
    importer = MonarchImporter(db)
    # Work inside a savepoint so autocreated entities vanish on rollback.
    try:
        summary = importer.ingest(payload)
    finally:
        db.rollback()

    return MonarchPreviewResponse(
        files=[_report_to_schema(f) for f in summary.files],
        would_import=summary.transactions_added,
        assets_would_create=summary.assets_created,
        liabilities_would_create=summary.liabilities_created,
    )


@router.post("/commit", response_model=MonarchCommitResponse)
async def commit_import(
    db: DbSession,
    files: list[UploadFile] = File(...),
) -> MonarchCommitResponse:
    payload = await _collect_files(files)
    importer = MonarchImporter(db)
    try:
        summary = importer.ingest(payload)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - surface to client
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc

    return MonarchCommitResponse(
        files=[_report_to_schema(f) for f in summary.files],
        transactions_added=summary.transactions_added,
        assets_created=summary.assets_created,
        liabilities_created=summary.liabilities_created,
    )
