"""Monarch Money CSV import API.

Endpoints:

* ``POST /v1/monarch-import/preview`` — parse + classify files (any
  mix of transactions + balances CSVs), return a per-file summary
  without touching the database.
* ``POST /v1/monarch-import/commit`` — parse, classify, and persist to
  the database with per-account Wealthsimple cutover + canonical-hash
  cross-source dedup for transactions and upsert-by-date semantics for
  balance snapshots.

The preview endpoint uses a savepoint so that any autocreated accounts
computed during the dry run are rolled back — users see the same
"assets_created" / "liabilities_created" lists without any
side-effects.

The API transparently routes each file to the right importer by
inspecting its header row, so users can drop both Monarch CSV exports
at once.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.db.session import DbSession
from backend.models.monarch_import_schemas import (
    MonarchBalancesCommitResponse,
    MonarchBalancesFileReport,
    MonarchBalancesPreviewResponse,
    MonarchCommitResponse,
    MonarchFileReport,
    MonarchMixedCommitResponse,
    MonarchMixedPreviewResponse,
    MonarchPreviewResponse,
)
from backend.services.monarch.balances_importer import (
    BalancesFileReport,
    MonarchBalancesImporter,
)
from backend.services.monarch.balances_parser import looks_like_balances_header
from backend.services.monarch.importer import FileReport, MonarchImporter

router = APIRouter(prefix="/v1/monarch-import", tags=["monarch-import"])

MAX_FILES = 10  # allow tx + balances from the same export batch
MAX_BYTES = 25 * 1024 * 1024  # 25MB / file — Monarch exports can get large


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


def _split_by_kind(
    payload: list[tuple[str, str]],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Route each file to its importer based on the header row.

    Returns ``(transaction_files, balance_files)``.
    """
    tx: list[tuple[str, str]] = []
    bal: list[tuple[str, str]] = []
    for filename, content in payload:
        first_line = content.split("\n", 1)[0] if content else ""
        if looks_like_balances_header(first_line):
            bal.append((filename, content))
        else:
            tx.append((filename, content))
    return tx, bal


# ---------------------------------------------------------------------------
# Report -> schema shims
# ---------------------------------------------------------------------------


def _tx_report_to_schema(r: FileReport) -> MonarchFileReport:
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


def _bal_report_to_schema(r: BalancesFileReport) -> MonarchBalancesFileReport:
    return MonarchBalancesFileReport(
        filename=r.filename,
        header_ok=r.header_ok,
        rows_seen=r.rows_seen,
        inserted=r.inserted,
        updated=r.updated,
        skipped_pseudo=r.skipped_pseudo,
        skipped_foreign=r.skipped_foreign,
        skipped_unknown_account=r.skipped_unknown_account,
        assets_created=r.assets_created,
        liabilities_created=r.liabilities_created,
        assets_touched=sorted(r.assets_touched),
        liabilities_touched=sorted(r.liabilities_touched),
        warnings=r.warnings,
    )


# ---------------------------------------------------------------------------
# Unified endpoints (auto-routing)
# ---------------------------------------------------------------------------


@router.post("/preview", response_model=MonarchMixedPreviewResponse)
async def preview(
    db: DbSession,
    files: list[UploadFile] = File(...),
) -> MonarchMixedPreviewResponse:
    payload = await _collect_files(files)
    tx_payload, bal_payload = _split_by_kind(payload)

    tx_importer = MonarchImporter(db)
    bal_importer = MonarchBalancesImporter(db)
    try:
        tx_summary = tx_importer.ingest(tx_payload) if tx_payload else None
        bal_summary = bal_importer.ingest(bal_payload) if bal_payload else None
    finally:
        db.rollback()

    tx_response = MonarchPreviewResponse(
        files=[_tx_report_to_schema(f) for f in (tx_summary.files if tx_summary else [])],
        would_import=tx_summary.transactions_added if tx_summary else 0,
        assets_would_create=tx_summary.assets_created if tx_summary else [],
        liabilities_would_create=tx_summary.liabilities_created if tx_summary else [],
    )
    bal_response = MonarchBalancesPreviewResponse(
        files=[_bal_report_to_schema(f) for f in (bal_summary.files if bal_summary else [])],
        would_insert=bal_summary.inserted if bal_summary else 0,
        would_update=bal_summary.updated if bal_summary else 0,
        assets_would_create=bal_summary.assets_created if bal_summary else [],
        liabilities_would_create=bal_summary.liabilities_created if bal_summary else [],
    )
    return MonarchMixedPreviewResponse(transactions=tx_response, balances=bal_response)


@router.post("/commit", response_model=MonarchMixedCommitResponse)
async def commit_import(
    db: DbSession,
    files: list[UploadFile] = File(...),
) -> MonarchMixedCommitResponse:
    payload = await _collect_files(files)
    tx_payload, bal_payload = _split_by_kind(payload)

    try:
        tx_summary = (
            MonarchImporter(db).ingest(tx_payload) if tx_payload else None
        )
        bal_summary = (
            MonarchBalancesImporter(db).ingest(bal_payload) if bal_payload else None
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 — surface to client
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc

    tx_response = MonarchCommitResponse(
        files=[_tx_report_to_schema(f) for f in (tx_summary.files if tx_summary else [])],
        transactions_added=tx_summary.transactions_added if tx_summary else 0,
        assets_created=tx_summary.assets_created if tx_summary else [],
        liabilities_created=tx_summary.liabilities_created if tx_summary else [],
    )
    bal_response = MonarchBalancesCommitResponse(
        files=[_bal_report_to_schema(f) for f in (bal_summary.files if bal_summary else [])],
        balances_inserted=bal_summary.inserted if bal_summary else 0,
        balances_updated=bal_summary.updated if bal_summary else 0,
        assets_created=bal_summary.assets_created if bal_summary else [],
        liabilities_created=bal_summary.liabilities_created if bal_summary else [],
    )
    return MonarchMixedCommitResponse(transactions=tx_response, balances=bal_response)
