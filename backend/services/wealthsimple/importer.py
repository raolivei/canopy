"""Wealthsimple CSV importer: writes parsed rows into the Canopy schema.

Responsibilities:

- Classify the file via :func:`parse_filename`.
- Parse rows via :func:`parse_rows`.
- Upsert an :class:`Asset` (investments + cash) or :class:`Liability`
  (credit card + LOC).
- Emit :class:`Transaction` rows for all money movements, :class:`Lot` and
  :class:`Dividend` rows for BUY/SELL/DIV, and end-of-statement balance
  snapshots (:class:`AccountBalanceHistory` or
  :class:`LiabilityBalanceHistory`).
- Every ingested row is hashed into :class:`ImportedEvent` so re-importing
  the same file is a no-op.
"""

from __future__ import annotations

import hashlib
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType
from backend.db.models.dividend import Dividend, DividendType
from backend.db.models.imported_event import ImportedEvent
from backend.db.models.liability import (
    Liability,
    LiabilityBalanceHistory,
    LiabilityType,
)
from backend.db.models.lot import Lot
from backend.db.models.transaction import Transaction, TransactionType
from backend.services.canonical_hash import (
    canonical_event_hash,
    entity_key_for_asset,
    entity_key_for_liability,
)
from backend.services.wealthsimple.description_parser import (
    parse_buy,
    parse_direct_deposit,
    parse_div,
    parse_sell,
    parse_share_transfer,
)
from backend.services.wealthsimple.filename_parser import (
    AccountClass,
    WsAccountKind,
    WsFileMeta,
    parse_filename,
)
from backend.services.wealthsimple.row_parser import (
    ParsedRow,
    RowKind,
    ShapeKind,
    iter_rows,
    parse_shape_a,
    parse_shape_b,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

SOURCE = "wealthsimple"
INSTITUTION = "Wealthsimple"


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class FileReport:
    filename: str
    meta: WsFileMeta
    shape: ShapeKind = ShapeKind.UNKNOWN
    rows_seen: int = 0
    rows_imported: int = 0
    rows_duplicate: int = 0
    rows_unknown: int = 0
    by_kind: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None

    @property
    def account_display(self) -> str:
        if self.meta.account_number:
            return f"{self.meta.account_label} ({self.meta.account_number})"
        return self.meta.account_label

    def bump_kind(self, kind: RowKind) -> None:
        self.by_kind[kind.value] = self.by_kind.get(kind.value, 0) + 1


@dataclass
class ImportSummary:
    files: list[FileReport] = field(default_factory=list)
    assets_touched: set[str] = field(default_factory=set)
    liabilities_touched: set[str] = field(default_factory=set)
    lots_added: int = 0
    dividends_added: int = 0
    transactions_added: int = 0
    account_snapshots_added: int = 0
    liability_snapshots_added: int = 0
    duplicates_skipped: int = 0

    def total_imported(self) -> int:
        return sum(f.rows_imported for f in self.files)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


_KIND_TO_ASSET_TYPE: dict[WsAccountKind, AssetType] = {
    WsAccountKind.CHEQUING: AssetType.BANK_CHECKING,
    WsAccountKind.TFSA: AssetType.RETIREMENT_TFSA,
    WsAccountKind.TFSA_LONG: AssetType.RETIREMENT_TFSA,
    WsAccountKind.FHSA: AssetType.RETIREMENT_FHSA,
    WsAccountKind.RRSP: AssetType.RETIREMENT_RRSP,
    WsAccountKind.CRYPTO: AssetType.CRYPTO,
    WsAccountKind.EMERGING: AssetType.OTHER,
}


_KIND_TO_LIABILITY_TYPE: dict[WsAccountKind, LiabilityType] = {
    WsAccountKind.CREDIT_CARD: LiabilityType.CREDIT_CARD,
    WsAccountKind.LINE_OF_CREDIT: LiabilityType.LINE_OF_CREDIT,
}


def _hash_event(
    account_key: str,
    occurred_on: date,
    raw_code: str,
    amount: Decimal,
    description: str,
) -> str:
    payload = f"{SOURCE}|{account_key}|{occurred_on.isoformat()}|{raw_code}|{amount}|{description}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _statement_end(statement_start: Optional[date], fallback: date) -> date:
    """Return the last day of the statement's month.

    Wealthsimple names files with the statement period's *start* date
    (typically the 1st). The end-of-statement snapshot we record is the
    last calendar day of that same month.
    """
    anchor = statement_start or fallback
    last_day = monthrange(anchor.year, anchor.month)[1]
    return date(anchor.year, anchor.month, last_day)


def _row_to_transaction_type(kind: RowKind, amount: Decimal) -> str:
    if kind == RowKind.BUY:
        return TransactionType.BUY.value
    if kind == RowKind.SELL:
        return TransactionType.SELL.value
    if kind in {RowKind.DIV, RowKind.INTEREST, RowKind.GIVEAWAY, RowKind.DEPOSIT, RowKind.CONTRIB}:
        return TransactionType.INCOME.value
    if kind in {RowKind.FEE, RowKind.TAX, RowKind.WITHDRAW, RowKind.CC_FEE, RowKind.CC_INTEREST}:
        return TransactionType.EXPENSE.value
    if kind == RowKind.CC_PURCHASE:
        return TransactionType.EXPENSE.value
    if kind == RowKind.CC_REFUND:
        return TransactionType.INCOME.value
    if kind == RowKind.CC_PAYMENT:
        return TransactionType.TRANSFER.value
    if kind in {RowKind.TRANSFER_IN, RowKind.TRANSFER_OUT, RowKind.SHARE_TRANSFER}:
        return TransactionType.TRANSFER.value
    if amount >= 0:
        return TransactionType.INCOME.value
    return TransactionType.EXPENSE.value


_KIND_CATEGORY: dict[RowKind, str] = {
    RowKind.DIV: "dividend",
    RowKind.INTEREST: "interest",
    RowKind.FEE: "fee",
    RowKind.TAX: "tax",
    RowKind.CONTRIB: "contribution",
    RowKind.WITHDRAW: "withdrawal",
    RowKind.DEPOSIT: "deposit",
    RowKind.TRANSFER_IN: "transfer",
    RowKind.TRANSFER_OUT: "transfer",
    RowKind.SHARE_TRANSFER: "share_transfer",
    RowKind.GIVEAWAY: "giveaway",
    RowKind.BUY: "investment",
    RowKind.SELL: "investment",
    RowKind.CC_PURCHASE: "credit_card_purchase",
    RowKind.CC_REFUND: "credit_card_refund",
    RowKind.CC_PAYMENT: "credit_card_payment",
    RowKind.CC_FEE: "credit_card_fee",
    RowKind.CC_INTEREST: "credit_card_interest",
}


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


class WealthsimpleImporter:
    """Ingest Wealthsimple CSVs into the Canopy schema.

    The importer is stateless beyond the provided :class:`Session`. Each
    ``ingest`` call holds a single DB transaction open: callers commit or
    roll back based on the returned :class:`ImportSummary`.
    """

    def __init__(self, db: Session, *, dry_run: bool = False) -> None:
        self.db = db
        self.dry_run = dry_run
        self._event_cache: set[str] = set()
        self._canonical_cache: set[str] = set()

    def ingest(self, files: Iterable[tuple[str, str]]) -> ImportSummary:
        summary = ImportSummary()
        for filename, content in files:
            report = self._ingest_file(filename, content, summary)
            summary.files.append(report)
        return summary

    # ------------------------------------------------------------------
    # File-level
    # ------------------------------------------------------------------

    def _ingest_file(self, filename: str, content: str, summary: ImportSummary) -> FileReport:
        meta = parse_filename(filename)
        report = FileReport(filename=meta.filename, meta=meta)

        if meta.is_skipped:
            report.skipped = True
            report.skip_reason = meta.skip_reason
            return report

        if meta.account_number is None and meta.account_kind not in {
            WsAccountKind.CREDIT_CARD,
        }:
            report.skipped = True
            report.skip_reason = "Could not extract account number from filename"
            return report

        # Pre-resolve the account key used for dedup hashing
        account_key = meta.account_number or f"ws-{meta.account_kind.value}"

        # Iterate rows
        last_row_by_currency: dict[str, ParsedRow] = {}
        cc_delta = Decimal("0")
        cc_last_post: Optional[date] = None
        parsed_rows: list[ParsedRow] = []
        detected_shape = ShapeKind.UNKNOWN

        for shape, _header, row_dict in iter_rows(content):
            detected_shape = shape
            parsed: Optional[ParsedRow]
            if shape == ShapeKind.SHAPE_A:
                parsed = parse_shape_a(row_dict)
            elif shape == ShapeKind.SHAPE_B:
                parsed = parse_shape_b(row_dict)
            else:
                parsed = None
            if parsed is None:
                continue
            report.rows_seen += 1
            parsed_rows.append(parsed)
            if parsed.kind == RowKind.UNKNOWN:
                report.rows_unknown += 1
                report.warnings.append(
                    f"Unknown transaction code '{parsed.raw_code}' on {parsed.occurred_on.isoformat()}"
                )
            # Track the last row per currency (for end-of-statement snapshot)
            prev = last_row_by_currency.get(parsed.currency)
            if prev is None or parsed.occurred_on >= prev.occurred_on:
                last_row_by_currency[parsed.currency] = parsed
            # Credit-card running delta
            if meta.account_kind == WsAccountKind.CREDIT_CARD:
                cc_delta += parsed.amount
                if parsed.post_date is not None and (cc_last_post is None or parsed.post_date >= cc_last_post):
                    cc_last_post = parsed.post_date

        report.shape = detected_shape
        if detected_shape == ShapeKind.UNKNOWN:
            report.skipped = True
            report.skip_reason = "CSV header did not match any known shape"
            return report

        # Resolve target asset/liability once, outside the row loop
        asset: Optional[Asset] = None
        liability: Optional[Liability] = None
        if meta.account_class in {AccountClass.INVESTMENT, AccountClass.CASH}:
            asset = self._upsert_account_asset(meta)
            summary.assets_touched.add(asset.symbol)
        elif meta.account_class == AccountClass.DEBT:
            liability = self._upsert_liability(meta)
            summary.liabilities_touched.add(liability.name)

        # Compute the cross-source entity key once per file - every row in
        # the same statement resolves to the same Canopy entity.
        entity_key: Optional[str] = None
        if asset is not None:
            entity_key = entity_key_for_asset(asset.id)
        elif liability is not None:
            entity_key = entity_key_for_liability(liability.id)

        # Write rows
        for parsed in parsed_rows:
            hashed = _hash_event(
                account_key=account_key,
                occurred_on=parsed.occurred_on,
                raw_code=parsed.raw_code,
                amount=parsed.amount,
                description=parsed.description,
            )
            if hashed in self._event_cache or self._event_exists(hashed):
                report.rows_duplicate += 1
                summary.duplicates_skipped += 1
                continue

            canonical = (
                canonical_event_hash(entity_key, parsed.occurred_on, parsed.amount) if entity_key is not None else None
            )
            if canonical is not None and (canonical in self._canonical_cache or self._canonical_exists(canonical)):
                report.rows_duplicate += 1
                summary.duplicates_skipped += 1
                continue

            self._event_cache.add(hashed)
            if canonical is not None:
                self._canonical_cache.add(canonical)

            report.bump_kind(parsed.kind)

            if asset is not None:
                self._write_investment_or_cash_row(
                    asset=asset,
                    meta=meta,
                    row=parsed,
                    summary=summary,
                    event_hash=hashed,
                    canonical_hash=canonical,
                    filename=meta.filename,
                )
            elif liability is not None:
                self._write_debt_row(
                    liability=liability,
                    meta=meta,
                    row=parsed,
                    summary=summary,
                    event_hash=hashed,
                    canonical_hash=canonical,
                    filename=meta.filename,
                )
            report.rows_imported += 1

        # End-of-statement snapshots: one row per (asset, as_of_date, currency).
        # Wealthsimple investment accounts can carry both a CAD and a USD cash
        # sub-balance (e.g. TFSA holding US stocks); we persist both. Net-worth
        # aggregation filters to CAD to avoid mixing units.
        if asset is not None and last_row_by_currency:
            for currency, row in last_row_by_currency.items():
                if row.balance is None:
                    continue
                as_of = _statement_end(meta.statement_period_start, row.occurred_on)
                added = self._upsert_account_snapshot(
                    asset_id=asset.id,
                    as_of_date=as_of,
                    balance=row.balance,
                    currency=currency,
                )
                if added:
                    summary.account_snapshots_added += 1

        if liability is not None:
            if meta.account_kind == WsAccountKind.LINE_OF_CREDIT and last_row_by_currency:
                for _cur, row in last_row_by_currency.items():
                    if row.balance is None:
                        continue
                    added = self._upsert_liability_snapshot(
                        liability_id=liability.id,
                        balance=row.balance,
                        recorded_at=_statement_end(meta.statement_period_start, row.occurred_on),
                        is_statement_balance=True,
                    )
                    if added:
                        summary.liability_snapshots_added += 1
                    # LOC balance column is the outstanding principal
                    liability.current_balance = row.balance
                    liability.balance_updated_at = datetime.now(timezone.utc)
            elif meta.account_kind == WsAccountKind.CREDIT_CARD:
                # Recompute cumulative balance across *all* imported CC rows to
                # date (in case earlier statements were imported too). Sum of
                # all Transaction.amount rows for this liability is the delta;
                # add opening_balance for pre-history correction.
                ledger_delta = self._credit_card_ledger_delta(liability.id)
                liability.current_balance = (liability.opening_balance or Decimal("0")) + ledger_delta
                liability.balance_updated_at = datetime.now(timezone.utc)
                if cc_last_post is not None:
                    added = self._upsert_liability_snapshot(
                        liability_id=liability.id,
                        balance=liability.current_balance,
                        recorded_at=datetime.combine(cc_last_post, datetime.min.time(), tzinfo=timezone.utc),
                        is_statement_balance=True,
                    )
                    if added:
                        summary.liability_snapshots_added += 1

        return report

    # ------------------------------------------------------------------
    # Upserts
    # ------------------------------------------------------------------

    def _upsert_account_asset(self, meta: WsFileMeta) -> Asset:
        symbol = f"WS:{meta.account_number}"
        existing = self.db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
        if existing is not None:
            # Keep the most informative name
            if existing.name != meta.account_label:
                existing.name = meta.account_label
            existing.sync_source = SOURCE
            existing.institution = INSTITUTION
            return existing

        asset_type = _KIND_TO_ASSET_TYPE.get(meta.account_kind, AssetType.OTHER)
        asset = Asset(
            symbol=symbol,
            name=meta.account_label,
            asset_type=asset_type,
            currency="CAD",
            institution=INSTITUTION,
            country="CA",
            sync_source=SOURCE,
            external_account_id=meta.account_number,
        )
        self.db.add(asset)
        self.db.flush()
        return asset

    def _upsert_ticker_asset(self, ticker: str, name: str, meta: WsFileMeta) -> Asset:
        existing = self.db.execute(select(Asset).where(Asset.symbol == ticker)).scalar_one_or_none()
        if existing is not None:
            return existing
        asset_type = (
            AssetType.CRYPTO
            if meta.account_kind == WsAccountKind.CRYPTO
            else AssetType.ETF
            if ticker.endswith((".B", ".F")) or "." in ticker
            else AssetType.STOCK
        )
        asset = Asset(
            symbol=ticker,
            name=name or ticker,
            asset_type=asset_type,
            currency="USD",  # best-effort default; we don't know listing currency
            institution=INSTITUTION,
            sync_source=SOURCE,
        )
        self.db.add(asset)
        self.db.flush()
        return asset

    def _upsert_liability(self, meta: WsFileMeta) -> Liability:
        name = (
            "Wealthsimple Credit Card"
            if meta.account_kind == WsAccountKind.CREDIT_CARD
            else f"Wealthsimple {meta.account_label}"
        )
        last4 = None
        if meta.account_number:
            last4 = meta.account_number[-4:] if len(meta.account_number) >= 4 else None
        existing = self.db.execute(
            select(Liability).where(
                Liability.institution == INSTITUTION,
                Liability.name == name,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        liability = Liability(
            name=name,
            institution=INSTITUTION,
            liability_type=_KIND_TO_LIABILITY_TYPE[meta.account_kind].value,
            account_number_last4=last4,
            currency="CAD",
            country="CA",
        )
        self.db.add(liability)
        self.db.flush()
        return liability

    # ------------------------------------------------------------------
    # Row writers
    # ------------------------------------------------------------------

    def _write_investment_or_cash_row(
        self,
        asset: Asset,
        meta: WsFileMeta,
        row: ParsedRow,
        summary: ImportSummary,
        event_hash: str,
        canonical_hash: Optional[str],
        filename: str,
    ) -> None:
        # Always write a Transaction
        tx = self._create_transaction(row=row, account_label=meta.account_label)
        self.db.add(tx)
        self.db.flush()
        summary.transactions_added += 1
        self._record_event(
            hashed=event_hash,
            canonical=canonical_hash,
            target_table="transactions",
            target_id=tx.id,
            filename=filename,
        )

        # Enrich with Lot / Dividend for investment rows
        if row.kind == RowKind.BUY:
            info = parse_buy(row.description)
            if info is not None:
                ticker_asset = self._upsert_ticker_asset(info.ticker, info.name, meta)
                lot = Lot(
                    asset_id=ticker_asset.id,
                    quantity=info.shares,
                    price_per_unit=info.price,
                    fees=Decimal("0"),
                    purchase_date=info.executed_at,
                    account=meta.account_label,
                )
                self.db.add(lot)
                self.db.flush()
                summary.lots_added += 1
                tx.ticker = info.ticker
                tx.shares = info.shares
                tx.price_per_share = info.price
        elif row.kind == RowKind.SELL:
            info = parse_sell(row.description)
            if info is not None:
                tx.ticker = info.ticker
                tx.shares = info.shares
                tx.price_per_share = info.price
                self._mark_lots_sold(
                    ticker=info.ticker,
                    quantity=info.shares,
                    price=info.price,
                    sold_on=info.executed_at,
                )
        elif row.kind == RowKind.DIV:
            info = parse_div(row.description)
            if info is not None:
                ticker_asset = self._upsert_ticker_asset(info.ticker, info.name, meta)
                div = Dividend(
                    asset_id=ticker_asset.id,
                    amount=row.amount,
                    payment_date=info.pay_date,
                    dividend_type=DividendType.CASH,
                )
                self.db.add(div)
                self.db.flush()
                summary.dividends_added += 1
                tx.ticker = info.ticker
        elif row.kind == RowKind.SHARE_TRANSFER:
            info = parse_share_transfer(row.description)
            if info is not None:
                tx.ticker = info.ticker
                tx.shares = info.shares
        elif row.kind == RowKind.DEPOSIT:
            dd = parse_direct_deposit(row.description)
            if dd is not None:
                tx.merchant = dd.employer

    def _write_debt_row(
        self,
        liability: Liability,
        meta: WsFileMeta,
        row: ParsedRow,
        summary: ImportSummary,
        event_hash: str,
        canonical_hash: Optional[str],
        filename: str,
    ) -> None:
        tx = self._create_transaction(row=row, account_label=liability.name)
        self.db.add(tx)
        self.db.flush()
        summary.transactions_added += 1
        self._record_event(
            hashed=event_hash,
            canonical=canonical_hash,
            target_table="transactions",
            target_id=tx.id,
            filename=filename,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_transaction(self, row: ParsedRow, account_label: str) -> Transaction:
        tx_type = _row_to_transaction_type(row.kind, row.amount)
        category = _KIND_CATEGORY.get(row.kind)
        occurred_at = datetime.combine(row.occurred_on, datetime.min.time(), tzinfo=timezone.utc)
        return Transaction(
            description=row.description[:500] or row.raw_code or "Wealthsimple row",
            amount=row.amount,
            currency=row.currency,
            type=tx_type,
            date=occurred_at,
            category=category,
            account=account_label,
            original_statement=row.description[:500] or None,
            import_source=SOURCE,
        )

    def _mark_lots_sold(
        self,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        sold_on: date,
    ) -> None:
        """FIFO-consume open lots of ``ticker`` until ``quantity`` is covered.

        Partial lot sales split the remaining quantity onto a fresh lot so
        cost-basis math downstream stays accurate.
        """
        asset = self.db.execute(select(Asset).where(Asset.symbol == ticker)).scalar_one_or_none()
        if asset is None:
            return
        remaining = quantity
        lots = (
            self.db.execute(
                select(Lot)
                .where(Lot.asset_id == asset.id, Lot.is_sold.is_(False))
                .order_by(Lot.purchase_date.asc(), Lot.id.asc())
            )
            .scalars()
            .all()
        )
        for lot in lots:
            if remaining <= 0:
                break
            if lot.quantity <= remaining:
                lot.is_sold = True
                lot.sold_date = sold_on
                lot.sold_price_per_unit = price
                remaining -= lot.quantity
            else:
                # Split: mark the consumed slice sold, leave a new unsold lot
                consumed = remaining
                left = lot.quantity - consumed
                lot.quantity = consumed
                lot.is_sold = True
                lot.sold_date = sold_on
                lot.sold_price_per_unit = price
                new_lot = Lot(
                    asset_id=lot.asset_id,
                    quantity=left,
                    price_per_unit=lot.price_per_unit,
                    fees=Decimal("0"),
                    purchase_date=lot.purchase_date,
                    account=lot.account,
                )
                self.db.add(new_lot)
                remaining = Decimal("0")

    def _event_exists(self, hashed: str) -> bool:
        return (
            self.db.execute(select(ImportedEvent.id).where(ImportedEvent.hash == hashed)).scalar_one_or_none()
            is not None
        )

    def _canonical_exists(self, canonical: str) -> bool:
        return (
            self.db.execute(
                select(ImportedEvent.id).where(ImportedEvent.canonical_hash == canonical)
            ).scalar_one_or_none()
            is not None
        )

    def _record_event(
        self,
        hashed: str,
        canonical: Optional[str],
        target_table: str,
        target_id: Optional[int],
        filename: str,
    ) -> None:
        self.db.add(
            ImportedEvent(
                hash=hashed,
                canonical_hash=canonical,
                source=SOURCE,
                target_table=target_table,
                target_id=target_id,
                file_name=filename,
            )
        )

    def _upsert_account_snapshot(
        self,
        asset_id: int,
        as_of_date: date,
        balance: Decimal,
        currency: str,
    ) -> bool:
        # Dedupe key is (asset_id, as_of_date, currency) — see
        # ``uq_account_balance_asset_date_currency`` on the model.
        existing = self.db.execute(
            select(AccountBalanceHistory).where(
                AccountBalanceHistory.asset_id == asset_id,
                AccountBalanceHistory.as_of_date == as_of_date,
                AccountBalanceHistory.currency == currency,
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.balance = balance
            return False
        self.db.add(
            AccountBalanceHistory(
                asset_id=asset_id,
                as_of_date=as_of_date,
                balance=balance,
                currency=currency,
                source="wealthsimple_csv",
            )
        )
        return True

    def _upsert_liability_snapshot(
        self,
        liability_id: int,
        balance: Decimal,
        recorded_at: date | datetime,
        is_statement_balance: bool,
    ) -> bool:
        when = (
            recorded_at
            if isinstance(recorded_at, datetime)
            else datetime.combine(recorded_at, datetime.min.time(), tzinfo=timezone.utc)
        )
        # Simple idempotency: skip if a row with the same liability + day + balance exists.
        existing = (
            self.db.execute(
                select(LiabilityBalanceHistory).where(
                    LiabilityBalanceHistory.liability_id == liability_id,
                    LiabilityBalanceHistory.balance == balance,
                )
            )
            .scalars()
            .all()
        )
        for row in existing:
            if row.recorded_at is not None and row.recorded_at.date() == when.date():
                return False
        self.db.add(
            LiabilityBalanceHistory(
                liability_id=liability_id,
                balance=balance,
                recorded_at=when,
                is_statement_balance=is_statement_balance,
            )
        )
        return True

    def _credit_card_ledger_delta(self, liability_id: int) -> Decimal:
        """Sum of all Transaction.amount rows currently tied to this CC.

        Credit-card CSVs omit the balance column, so the absolute balance is
        reconstructed from the cumulative ledger every time we ingest a new
        statement file.
        """
        # We tag CC transactions with ``account=<liability.name>`` so the
        # ledger delta is ``sum(Transaction.amount where account=<name>)``.
        liability = self.db.get(Liability, liability_id)
        if liability is None:
            return Decimal("0")
        total = self.db.execute(select(Transaction.amount).where(Transaction.account == liability.name)).scalars().all()
        return sum(total, Decimal("0"))
