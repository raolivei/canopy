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
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType
from backend.db.models.liability import Liability, LiabilityBalanceHistory
from backend.db.session import DbSession
from backend.models.wealthsimple_import_schemas import (
    NetWorthPoint,
    NetWorthSlice,
    NetWorthTimelineResponse,
    WsAccountSummary,
    WsCommitResponse,
    WsFileClassification,
    WsPreviewResponse,
    WsSubBalance,
)
from backend.services import fx as fx_service
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
    """Return every Wealthsimple account with its CAD and USD sub-balances.

    A single brokerage account often carries a CAD and a USD cash
    sub-balance on the same statement end-date (e.g. a TFSA holding US
    ETFs). We surface both via ``balances_by_currency`` so the Accounts
    page can show dual figures Questrade-style; the legacy
    ``current_balance`` field still returns the CAD side for
    back-compat.
    """
    summaries: list[WsAccountSummary] = []

    assets = (
        db.execute(select(Asset).where(Asset.sync_source == "wealthsimple"))
        .scalars()
        .all()
    )
    for asset in assets:
        # One row per currency: the latest observation for each.
        per_ccy_rows = db.execute(
            select(
                AccountBalanceHistory.currency,
                AccountBalanceHistory.balance,
                AccountBalanceHistory.as_of_date,
            )
            .where(AccountBalanceHistory.asset_id == asset.id)
            .order_by(
                AccountBalanceHistory.currency,
                AccountBalanceHistory.as_of_date.desc(),
            )
        ).all()

        seen: set[str] = set()
        balances: list[WsSubBalance] = []
        for ccy, balance, as_of in per_ccy_rows:
            key = (ccy or "CAD").upper()
            if key in seen:
                continue
            seen.add(key)
            balances.append(
                WsSubBalance(currency=key, balance=balance, as_of_date=as_of)
            )

        # Legacy field: pick the CAD entry if present, else the first
        # balance we have.
        cad_entry = next((b for b in balances if b.currency == "CAD"), None)
        legacy_balance = cad_entry or (balances[0] if balances else None)

        summaries.append(
            WsAccountSummary(
                kind="asset",
                symbol_or_name=asset.symbol,
                display_name=asset.name,
                account_type=(
                    asset.asset_type.value
                    if hasattr(asset.asset_type, "value")
                    else str(asset.asset_type)
                ),
                institution=asset.institution or "Wealthsimple",
                currency=asset.currency,
                current_balance=legacy_balance.balance if legacy_balance else None,
                balance_updated_at=(
                    legacy_balance.as_of_date if legacy_balance else None
                ),
                balances_by_currency=balances,
            )
        )

    liabilities = (
        db.execute(select(Liability).where(Liability.institution == "Wealthsimple"))
        .scalars()
        .all()
    )
    for liab in liabilities:
        liab_balance = liab.current_balance or Decimal("0")
        liab_as_of = (
            liab.balance_updated_at.date() if liab.balance_updated_at is not None else None
        )
        summaries.append(
            WsAccountSummary(
                kind="liability",
                symbol_or_name=liab.name,
                display_name=liab.name,
                account_type=liab.liability_type,
                institution=liab.institution,
                currency=liab.currency,
                current_balance=liab_balance,
                balance_updated_at=liab_as_of,
                balances_by_currency=[
                    WsSubBalance(
                        currency=(liab.currency or "CAD").upper(),
                        balance=liab_balance,
                        as_of_date=liab_as_of,
                    )
                ],
            )
        )
    return summaries


@router.get("/networth-timeline", response_model=NetWorthTimelineResponse)
def networth_timeline(db: DbSession) -> NetWorthTimelineResponse:
    """Aggregate investments/cash/debt over time, by currency.

    Strategy:

    1. Pull every ``AccountBalanceHistory`` row (all currencies) and
       every ``LiabilityBalanceHistory`` row (currency from the parent
       ``Liability``).
    2. Group by (date, currency) and carry forward the most recent
       balance per account per currency so each date produces a full
       snapshot.
    3. For each date, produce four slices — CAD-only, USD-only, and
       two cross-currency combinations converted at the FX rate for
       that date (fallback: most-recent prior). The CAD slice is
       mirrored into the legacy top-level fields for back-compat.

    No data is filtered out any more: a USD sub-balance on a CAD TFSA
    shows up in the USD and Combined views, even when the underlying
    account is in Canada.
    """
    from collections import defaultdict
    from bisect import bisect_right

    from backend.db.models.fx_rate import FxRate

    # Load balances. Per-row currency lives on ``AccountBalanceHistory``;
    # for liabilities we use the parent ``Liability.currency`` since
    # ``LiabilityBalanceHistory`` has no currency column of its own.
    asset_rows = db.execute(
        select(
            AccountBalanceHistory.as_of_date,
            AccountBalanceHistory.asset_id,
            AccountBalanceHistory.balance,
            AccountBalanceHistory.currency,
            Asset.asset_type,
        ).join(Asset, Asset.id == AccountBalanceHistory.asset_id)
    ).all()

    liab_rows = db.execute(
        select(
            LiabilityBalanceHistory.recorded_at,
            LiabilityBalanceHistory.liability_id,
            LiabilityBalanceHistory.balance,
            Liability.currency,
        ).join(Liability, Liability.id == LiabilityBalanceHistory.liability_id)
    ).all()

    # Key = (currency, account_id). That lets the same underlying Asset
    # contribute to both the CAD and USD running totals when a statement
    # has both CAD and USD sub-balances for it.
    events: dict[date, dict[str, dict[tuple[str, int], Decimal]]] = defaultdict(
        lambda: {"inv": {}, "cash": {}, "debt": {}}
    )

    for as_of, asset_id, balance, ccy, asset_type in asset_rows:
        if as_of is None:
            continue
        currency = (ccy or "CAD").upper()
        if currency not in {"CAD", "USD"}:
            # Defensive: the schema only allows CAD/USD today, but a
            # mislabelled row shouldn't poison the aggregation.
            continue
        bucket = "cash" if asset_type in _CASH_TYPES else "inv"
        events[as_of][bucket][(currency, asset_id)] = Decimal(balance or 0)

    for recorded_at, liab_id, balance, ccy in liab_rows:
        if recorded_at is None:
            continue
        d = recorded_at.date() if hasattr(recorded_at, "date") else recorded_at
        currency = (ccy or "CAD").upper()
        if currency not in {"CAD", "USD"}:
            continue
        events[d]["debt"][(currency, liab_id)] = Decimal(balance or 0)

    # Pre-load FX rates for the whole window so per-point conversion is
    # O(log n) rather than n DB queries.
    fx_rows = (
        db.execute(
            select(FxRate.as_of_date, FxRate.rate)
            .where(FxRate.pair == "USDCAD")
            .order_by(FxRate.as_of_date)
        )
        .all()
    )
    fx_dates = [row[0] for row in fx_rows]
    fx_values = [row[1] for row in fx_rows]

    def _rate_on(d: date) -> Optional[Decimal]:
        if not fx_dates:
            return None
        idx = bisect_right(fx_dates, d)
        if idx == 0:
            # ``d`` is earlier than the first rate we know about. Use
            # the oldest observation rather than returning None — the
            # conversion will be approximate but non-zero, which is
            # what a user scrolling back through history expects.
            return fx_values[0]
        return fx_values[idx - 1]

    if not events:
        return NetWorthTimelineResponse(points=[])

    latest_rate_row = fx_service.get_latest_rate(db)

    sorted_dates = sorted(events.keys())
    # (currency, account_id) -> Decimal
    running_inv: dict[tuple[str, int], Decimal] = {}
    running_cash: dict[tuple[str, int], Decimal] = {}
    running_debt: dict[tuple[str, int], Decimal] = {}

    points: list[NetWorthPoint] = []
    for d in sorted_dates:
        running_inv.update(events[d]["inv"])
        running_cash.update(events[d]["cash"])
        running_debt.update(events[d]["debt"])

        def _sum_ccy(bag: dict[tuple[str, int], Decimal], ccy: str) -> Decimal:
            return sum(
                (v for (c, _aid), v in bag.items() if c == ccy), start=Decimal("0")
            )

        cad_inv = _sum_ccy(running_inv, "CAD")
        cad_cash = _sum_ccy(running_cash, "CAD")
        cad_debt = _sum_ccy(running_debt, "CAD")
        usd_inv = _sum_ccy(running_inv, "USD")
        usd_cash = _sum_ccy(running_cash, "USD")
        usd_debt = _sum_ccy(running_debt, "USD")

        rate = _rate_on(d)

        def _combine_cad(
            cad_amt: Decimal, usd_amt: Decimal, r: Optional[Decimal]
        ) -> Decimal:
            if r is None or r == 0:
                # Without FX we can't mix; fall back to the CAD slice
                # alone rather than pretending USD is zero'd at 1.0.
                return cad_amt
            return cad_amt + (usd_amt * r)

        def _combine_usd(
            cad_amt: Decimal, usd_amt: Decimal, r: Optional[Decimal]
        ) -> Decimal:
            if r is None or r == 0:
                return usd_amt
            return usd_amt + (cad_amt / r)

        cad_slice = NetWorthSlice(
            investments=cad_inv,
            cash=cad_cash,
            debt=cad_debt,
            net_worth=cad_inv + cad_cash - cad_debt,
            currency="CAD",
        )
        usd_slice = NetWorthSlice(
            investments=usd_inv,
            cash=usd_cash,
            debt=usd_debt,
            net_worth=usd_inv + usd_cash - usd_debt,
            currency="USD",
        )
        combined_cad_inv = _combine_cad(cad_inv, usd_inv, rate)
        combined_cad_cash = _combine_cad(cad_cash, usd_cash, rate)
        combined_cad_debt = _combine_cad(cad_debt, usd_debt, rate)
        combined_usd_inv = _combine_usd(cad_inv, usd_inv, rate)
        combined_usd_cash = _combine_usd(cad_cash, usd_cash, rate)
        combined_usd_debt = _combine_usd(cad_debt, usd_debt, rate)

        combined_cad_slice = NetWorthSlice(
            investments=combined_cad_inv,
            cash=combined_cad_cash,
            debt=combined_cad_debt,
            net_worth=combined_cad_inv + combined_cad_cash - combined_cad_debt,
            currency="CAD",
        )
        combined_usd_slice = NetWorthSlice(
            investments=combined_usd_inv,
            cash=combined_usd_cash,
            debt=combined_usd_debt,
            net_worth=combined_usd_inv + combined_usd_cash - combined_usd_debt,
            currency="USD",
        )

        points.append(
            NetWorthPoint(
                date=d,
                # Legacy top-level fields mirror the CAD-native slice,
                # keeping the pre-multi-currency API contract.
                investments=cad_slice.investments,
                cash=cad_slice.cash,
                debt=cad_slice.debt,
                net_worth=cad_slice.net_worth,
                cad=cad_slice,
                usd=usd_slice,
                combined_cad=combined_cad_slice,
                combined_usd=combined_usd_slice,
                fx_rate=rate,
            )
        )

    last = points[-1]
    return NetWorthTimelineResponse(
        points=points,
        latest_investments=last.investments,
        latest_cash=last.cash,
        latest_debt=last.debt,
        latest_net_worth=last.net_worth,
        latest_cad=last.cad,
        latest_usd=last.usd,
        latest_combined_cad=last.combined_cad,
        latest_combined_usd=last.combined_usd,
        fx_rate=latest_rate_row.rate if latest_rate_row is not None else None,
        fx_as_of_date=(
            latest_rate_row.as_of_date if latest_rate_row is not None else None
        ),
        fx_is_stale=fx_service.is_stale(latest_rate_row),
    )
