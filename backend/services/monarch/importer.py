"""Monarch CSV importer.

Given parsed :class:`MonarchRow` objects, this service:

1. Resolves each row's account to a Canopy :class:`Asset` or
   :class:`Liability` (creating one if missing).
2. Applies two independent layers of dedup against existing data:

   * **Layer 1 - per-account Wealthsimple cutover.** For each Canopy
     entity that already has Wealthsimple-sourced transactions, we
     compute ``min(Transaction.date)`` for that entity and drop any
     Monarch row on or after that date. WS owns that account from that
     point forward.

   * **Layer 2 - canonical-hash backstop.** Every row's
     ``(entity_key, date, amount)`` fingerprint is checked against the
     ``imported_events.canonical_hash`` column. A hit means the same
     real-world transaction has already been written, regardless of
     source.

3. Persists kept rows as :class:`Transaction` with ``import_source =
   'monarch_csv'`` and records an :class:`ImportedEvent` per row so
   re-importing the same file is a no-op.

The importer is transaction-agnostic - it writes via the session but
leaves ``commit`` / ``rollback`` to the caller (the API layer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Iterable, Optional

from backend.db.models.imported_event import ImportedEvent
from backend.db.models.transaction import Transaction, TransactionType
from backend.services.canonical_hash import (
    canonical_event_hash,
    entity_key_for_asset,
    entity_key_for_liability,
    source_event_hash,
)
from backend.services.monarch.accounts import ResolvedAccount, resolve_account
from backend.services.monarch.parser import (
    MonarchRow,
    ParseResult,
    parse_monarch_csv,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

SOURCE = "monarch_csv"


# ---------------------------------------------------------------------------
# Reporting dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FileReport:
    """Per-file outcome of a Monarch import."""

    filename: str
    header_ok: bool = False
    rows_seen: int = 0
    imported: int = 0
    # Dedup + skip counters
    skipped_pseudo: int = 0
    skipped_foreign: int = 0
    skipped_unknown_account: int = 0
    skipped_ws_covered: int = 0
    skipped_canonical_dup: int = 0
    skipped_source_dup: int = 0
    # Entities touched by this file
    assets_created: list[str] = field(default_factory=list)
    liabilities_created: list[str] = field(default_factory=list)
    assets_touched: set[str] = field(default_factory=set)
    liabilities_touched: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportSummary:
    """Aggregate summary across all files in one ingest() call."""

    files: list[FileReport] = field(default_factory=list)
    transactions_added: int = 0

    @property
    def assets_created(self) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for f in self.files:
            for n in f.assets_created:
                if n not in seen:
                    out.append(n)
                    seen.add(n)
        return out

    @property
    def liabilities_created(self) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for f in self.files:
            for n in f.liabilities_created:
                if n not in seen:
                    out.append(n)
                    seen.add(n)
        return out


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


class MonarchImporter:
    """Stateful helper that walks parsed rows and writes to the database."""

    def __init__(self, db: Session) -> None:
        self.db = db
        # Per-session caches for repeated lookups inside one ingest() call
        self._event_cache: set[str] = set()
        self._canonical_cache: set[str] = set()
        self._account_cache: dict[str, Optional[ResolvedAccount]] = {}
        self._ws_cutoff_cache: dict[str, Optional[date]] = {}

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def ingest(self, files: Iterable[tuple[str, str]]) -> ImportSummary:
        summary = ImportSummary()
        for filename, content in files:
            report = self._ingest_file(filename, content)
            summary.files.append(report)
            summary.transactions_added += report.imported
        return summary

    # ------------------------------------------------------------------
    # Per-file pipeline
    # ------------------------------------------------------------------

    def _ingest_file(self, filename: str, content: str) -> FileReport:
        report = FileReport(filename=filename)
        parsed: ParseResult = parse_monarch_csv(content)
        report.header_ok = parsed.header_ok
        report.warnings.extend(parsed.warnings)
        report.skipped_pseudo = parsed.skipped_pseudo
        report.skipped_foreign = parsed.skipped_foreign
        report.rows_seen = parsed.kept + parsed.skipped_pseudo + parsed.skipped_foreign + parsed.unknown_amount_rows

        if not parsed.header_ok:
            return report

        for row in parsed.rows:
            self._ingest_row(row, report)

        return report

    def _ingest_row(self, row: MonarchRow, report: FileReport) -> None:
        resolved = self._resolve_cached(row)
        if resolved is None:
            report.skipped_unknown_account += 1
            return

        if resolved.created:
            if resolved.asset is not None:
                if resolved.asset.name not in report.assets_created:
                    report.assets_created.append(resolved.asset.name)
            if resolved.liability is not None:
                if resolved.liability.name not in report.liabilities_created:
                    report.liabilities_created.append(resolved.liability.name)
            if resolved.note:
                report.warnings.append(f"Account '{row.account_label}': {resolved.note}")

        # Track which entities this file touched so the API can surface
        # them in the summary.
        if resolved.asset is not None:
            report.assets_touched.add(resolved.asset.name)
        if resolved.liability is not None:
            report.liabilities_touched.add(resolved.liability.name)

        entity_key = self._entity_key(resolved)

        # Layer 1: per-account Wealthsimple cutover.
        cutoff = self._ws_cutoff(resolved)
        if cutoff is not None and row.occurred_on >= cutoff:
            report.skipped_ws_covered += 1
            return

        # Layer 2: canonical-hash backstop (cross-source dedup).
        canonical = canonical_event_hash(entity_key, row.occurred_on, row.amount)
        if canonical in self._canonical_cache or self._canonical_exists(canonical):
            report.skipped_canonical_dup += 1
            return

        # Per-source fingerprint: catches re-uploads of the same Monarch file.
        source_hash = source_event_hash(
            SOURCE,
            row.account_label,
            row.occurred_on.isoformat(),
            row.amount,
            row.original_statement or row.merchant,
        )
        if source_hash in self._event_cache or self._source_exists(source_hash):
            report.skipped_source_dup += 1
            return

        tx = self._to_transaction(row, resolved)
        self.db.add(tx)
        self.db.flush()

        self.db.add(
            ImportedEvent(
                hash=source_hash,
                canonical_hash=canonical,
                source=SOURCE,
                target_table="transactions",
                target_id=tx.id,
                file_name=report.filename,
            )
        )
        self._event_cache.add(source_hash)
        self._canonical_cache.add(canonical)
        report.imported += 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_cached(self, row: MonarchRow) -> Optional[ResolvedAccount]:
        key = row.account_label
        if key in self._account_cache:
            return self._account_cache[key]
        resolved = resolve_account(
            self.db,
            label=row.account_label,
            account_class=row.account_class,
            last4=row.account_last4,
            currency=row.currency,
        )
        self._account_cache[key] = resolved
        return resolved

    @staticmethod
    def _entity_key(resolved: ResolvedAccount) -> str:
        if resolved.asset is not None:
            return entity_key_for_asset(resolved.asset.id)
        assert resolved.liability is not None  # noqa: S101 - invariant
        return entity_key_for_liability(resolved.liability.id)

    def _ws_cutoff(self, resolved: ResolvedAccount) -> Optional[date]:
        """Earliest WS-sourced transaction date for this Canopy entity.

        Computed once per entity per ingest() call. Used by Layer 1 to
        stop Monarch rows from colonising the time window where WS is
        the authoritative source.
        """
        name: Optional[str] = None
        if resolved.asset is not None:
            name = resolved.asset.name
        elif resolved.liability is not None:
            name = resolved.liability.name
        if name is None:
            return None
        if name in self._ws_cutoff_cache:
            return self._ws_cutoff_cache[name]

        min_date = self.db.execute(
            select(func.min(Transaction.date)).where(
                Transaction.import_source == "wealthsimple_csv",
                Transaction.account == name,
            )
        ).scalar_one()
        cutoff: Optional[date] = None
        if min_date is not None:
            cutoff = min_date.date() if hasattr(min_date, "date") else min_date
        self._ws_cutoff_cache[name] = cutoff
        return cutoff

    def _canonical_exists(self, canonical: str) -> bool:
        return (
            self.db.execute(
                select(ImportedEvent.id).where(ImportedEvent.canonical_hash == canonical)
            ).scalar_one_or_none()
            is not None
        )

    def _source_exists(self, hashed: str) -> bool:
        return (
            self.db.execute(select(ImportedEvent.id).where(ImportedEvent.hash == hashed)).scalar_one_or_none()
            is not None
        )

    @staticmethod
    def _to_transaction(row: MonarchRow, resolved: ResolvedAccount) -> Transaction:
        tx_type = _transaction_type_for(row)
        occurred_at = datetime.combine(row.occurred_on, time.min, tzinfo=timezone.utc)
        description = row.merchant or row.original_statement or "Monarch row"
        # Canopy is CAD + USD only. Any other currency is filtered
        # upstream by AccountClass.FOREIGN; everything that reaches here
        # is tagged CAD or USD.
        currency = row.currency if row.currency in {"CAD", "USD"} else "CAD"
        return Transaction(
            description=description[:500],
            amount=row.amount,
            currency=currency,
            type=tx_type,
            date=occurred_at,
            category=row.category[:100] if row.category else None,
            account=resolved.canopy_name,
            merchant=row.merchant[:200] if row.merchant else None,
            original_statement=row.original_statement[:500] if row.original_statement else None,
            notes=row.notes or None,
            tags=list(row.tags) if row.tags else None,
            import_source=SOURCE,
        )


def _transaction_type_for(row: MonarchRow) -> str:
    """Infer a Canopy TransactionType from a Monarch row.

    We don't try to be clever - Monarch's sign convention is good enough:

    * Positive amount -> income (or credit-card payment received)
    * Negative amount -> expense
    * Category containing 'transfer' -> transfer

    BUY/SELL detection from Monarch is out of scope; those rows land as
    generic expense/income and the Wealthsimple importer is the
    authoritative source for lot-level investment state.
    """
    cat = (row.category or "").lower()
    if "transfer" in cat or "credit card payment" in cat:
        return TransactionType.TRANSFER.value
    if row.amount > Decimal("0"):
        return TransactionType.INCOME.value
    return TransactionType.EXPENSE.value
