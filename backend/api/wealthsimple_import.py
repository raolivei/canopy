"""Wealthsimple CSV auto-import API.

Endpoints:

- ``POST /v1/wealthsimple-import/preview`` - classify + count rows without writing.
- ``POST /v1/wealthsimple-import/commit`` - classify and persist to the DB.
- ``GET /v1/wealthsimple-import/accounts`` - list known Wealthsimple accounts.
- ``GET /v1/wealthsimple-import/networth-timeline`` - combined investments/cash/debt series.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability, LiabilityBalanceHistory
from backend.db.session import DbSession
from backend.models.wealthsimple_import_schemas import (
    NetWorthPoint,
    NetWorthTimelineResponse,
    WsAccountSummary,
    WsCommitResponse,
    WsFileClassification,
    WsPreviewResponse,
)
from backend.services.wealthsimple.importer import (
    FileReport,
    ImportSummary,
    WealthsimpleImporter,
)

router = APIRouter(prefix="/v1/wealthsimple-import", tags=["wealthsimple-import"])

MAX_FILES = 40
MAX_BYTES = 5 * 1024 * 1024  # 5MB / file; monthly statements are well under this


def _report_to_schema(r: FileReport) -> WsFileClassification:
    return WsFileClassification(
        filename=r.filename,
        account_label=r.meta.account_label,
        account_kind=r.meta.account_kind.value,
        account_class=r.meta.account_class.value,
        account_number=r.meta.account_number,
        statement_period_start=r.meta.statement_period_start,
        shape=r.shape.value,
        skipped=r.skipped,
        skip_reason=r.skip_reason,
        rows_seen=r.rows_seen,
        rows_imported=r.rows_imported,
        rows_duplicate=r.rows_duplicate,
        rows_unknown=r.rows_unknown,
        by_kind=r.by_kind,
        warnings=r.warnings,
    )


async def _collect_files(
    files: list[UploadFile],
) -> list[tuple[str, str]]:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Too many files (max {MAX_FILES})")
    collected: list[tuple[str, str]] = []
    for upload in files:
        if not upload.filename:
            continue
        content_bytes = await upload.read()
        if len(content_bytes) > MAX_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"{upload.filename} exceeds {MAX_BYTES} bytes",
            )
        try:
            text = content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1")
        collected.append((upload.filename, text))
    return collected


@router.post("/preview", response_model=WsPreviewResponse)
async def preview(
    db: DbSession,
    files: list[UploadFile] = File(...),
) -> WsPreviewResponse:
    payload = await _collect_files(files)
    importer = WealthsimpleImporter(db, dry_run=True)
    summary = importer.ingest(payload)
    # Roll back anything the importer tried to stage.
    db.rollback()

    schemas = [_report_to_schema(f) for f in summary.files]
    return WsPreviewResponse(
        files=schemas,
        total_rows_seen=sum(f.rows_seen for f in schemas),
        total_would_import=sum(f.rows_imported for f in schemas),
        total_duplicates=sum(f.rows_duplicate for f in schemas),
    )


@router.post("/commit", response_model=WsCommitResponse)
async def commit_import(
    db: DbSession,
    files: list[UploadFile] = File(...),
) -> WsCommitResponse:
    payload = await _collect_files(files)
    importer = WealthsimpleImporter(db)
    try:
        summary: ImportSummary = importer.ingest(payload)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - surface to client
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc

    return WsCommitResponse(
        files=[_report_to_schema(f) for f in summary.files],
        assets_touched=sorted(summary.assets_touched),
        liabilities_touched=sorted(summary.liabilities_touched),
        transactions_added=summary.transactions_added,
        lots_added=summary.lots_added,
        dividends_added=summary.dividends_added,
        account_snapshots_added=summary.account_snapshots_added,
        liability_snapshots_added=summary.liability_snapshots_added,
        duplicates_skipped=summary.duplicates_skipped,
    )


# ---------------------------------------------------------------------------
# Read endpoints
# ---------------------------------------------------------------------------


_INVESTMENT_TYPES = {
    AssetType.RETIREMENT_RRSP,
    AssetType.RETIREMENT_TFSA,
    AssetType.RETIREMENT_FHSA,
    AssetType.RETIREMENT_DPSP,
    AssetType.CRYPTO,
    AssetType.STOCK,
    AssetType.ETF,
    AssetType.BOND,
    AssetType.OTHER,
}

_CASH_TYPES = {
    AssetType.BANK_ACCOUNT,
    AssetType.BANK_CHECKING,
    AssetType.BANK_SAVINGS,
    AssetType.CASH,
}


@router.get("/accounts", response_model=list[WsAccountSummary])
def list_accounts(db: DbSession) -> list[WsAccountSummary]:
    summaries: list[WsAccountSummary] = []

    assets = db.execute(select(Asset).where(Asset.sync_source == "wealthsimple")).scalars().all()
    for asset in assets:
        latest = db.execute(
            select(AccountBalanceHistory)
            .where(AccountBalanceHistory.asset_id == asset.id)
            .order_by(AccountBalanceHistory.as_of_date.desc())
            .limit(1)
        ).scalar_one_or_none()
        summaries.append(
            WsAccountSummary(
                kind="asset",
                symbol_or_name=asset.symbol,
                display_name=asset.name,
                account_type=asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type),
                institution=asset.institution or "Wealthsimple",
                currency=asset.currency,
                current_balance=latest.balance if latest else None,
                balance_updated_at=latest.as_of_date if latest else None,
            )
        )

    liabilities = db.execute(select(Liability).where(Liability.institution == "Wealthsimple")).scalars().all()
    for liab in liabilities:
        summaries.append(
            WsAccountSummary(
                kind="liability",
                symbol_or_name=liab.name,
                display_name=liab.name,
                account_type=liab.liability_type,
                institution=liab.institution,
                currency=liab.currency,
                current_balance=liab.current_balance,
                balance_updated_at=(liab.balance_updated_at.date() if liab.balance_updated_at is not None else None),
            )
        )
    return summaries


@router.get("/networth-timeline", response_model=NetWorthTimelineResponse)
def networth_timeline(db: DbSession) -> NetWorthTimelineResponse:
    """Aggregate investments/cash/debt over time.

    Strategy: collect every ``AccountBalanceHistory`` and
    ``LiabilityBalanceHistory`` row, group by date, and carry forward the
    most recent balance per account so each date produces a full snapshot.
    """
    # Snapshot balance-per-asset and classify by investment vs cash
    asset_rows = db.execute(
        select(
            AccountBalanceHistory.as_of_date,
            AccountBalanceHistory.asset_id,
            AccountBalanceHistory.balance,
            Asset.asset_type,
        ).join(Asset, Asset.id == AccountBalanceHistory.asset_id)
    ).all()

    liab_rows = db.execute(
        select(
            LiabilityBalanceHistory.recorded_at,
            LiabilityBalanceHistory.liability_id,
            LiabilityBalanceHistory.balance,
        )
    ).all()

    # Build per-date dictionaries of {asset_id: balance} and {liab_id: balance}
    # sorted chronologically, then carry forward.
    from collections import defaultdict

    events: dict[date, dict[str, dict[int, Decimal]]] = defaultdict(lambda: {"inv": {}, "cash": {}, "debt": {}})

    for as_of, asset_id, balance, asset_type in asset_rows:
        if as_of is None:
            continue
        bucket = "cash" if asset_type in _CASH_TYPES else "inv"
        events[as_of][bucket][asset_id] = Decimal(balance or 0)

    for recorded_at, liab_id, balance in liab_rows:
        if recorded_at is None:
            continue
        d = recorded_at.date() if hasattr(recorded_at, "date") else recorded_at
        events[d]["debt"][liab_id] = Decimal(balance or 0)

    if not events:
        return NetWorthTimelineResponse(points=[])

    sorted_dates = sorted(events.keys())
    running_inv: dict[int, Decimal] = {}
    running_cash: dict[int, Decimal] = {}
    running_debt: dict[int, Decimal] = {}

    points: list[NetWorthPoint] = []
    for d in sorted_dates:
        running_inv.update(events[d]["inv"])
        running_cash.update(events[d]["cash"])
        running_debt.update(events[d]["debt"])
        investments = sum(running_inv.values(), Decimal("0"))
        cash = sum(running_cash.values(), Decimal("0"))
        debt = sum(running_debt.values(), Decimal("0"))
        points.append(
            NetWorthPoint(
                date=d,
                investments=investments,
                cash=cash,
                debt=debt,
                net_worth=investments + cash - debt,
            )
        )

    last = points[-1]
    return NetWorthTimelineResponse(
        points=points,
        latest_investments=last.investments,
        latest_cash=last.cash,
        latest_debt=last.debt,
        latest_net_worth=last.net_worth,
    )
