"""Monarch *balances* CSV importer.

Given parsed :class:`BalanceRow` objects, this service:

1. Resolves each row's account to a Canopy :class:`Asset` or
   :class:`Liability` (creating one if missing — same resolver used by
   the transactions importer).
2. Upserts one row per ``(entity, date, currency)`` into
   ``AccountBalanceHistory`` (for assets) or ``LiabilityBalanceHistory``
   (for liabilities).
3. Returns a per-file report suitable for surfacing in the import UI.

Sign handling:

* Monarch reports liability balances as negative ("you owe $21,818" ->
  ``-21818.66``). The importer stores the **absolute** value so that
  Canopy's liability math (``sum(balance)``) keeps working the same way
  as for Wealthsimple imports.
* Asset balances are stored as-is (Monarch already reports them
  positive, and a zero / tiny negative from a pending transaction is
  fine to keep).

Idempotency:

* Re-uploading the same balances CSV updates existing rows in-place
  (no duplicates, no history rewriting).
* The importer is transaction-agnostic — it writes via the session but
  leaves ``commit`` / ``rollback`` to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from typing import Iterable, Optional

from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.liability import Liability, LiabilityBalanceHistory
from backend.services.monarch.accounts import ResolvedAccount, resolve_account
from backend.services.monarch.balances_parser import (
    BalanceRow,
    BalancesParseResult,
    parse_monarch_balances_csv,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

SOURCE = "monarch_csv"


# ---------------------------------------------------------------------------
# Reporting dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BalancesFileReport:
    """Per-file outcome of a Monarch balances import."""

    filename: str
    header_ok: bool = False
    rows_seen: int = 0
    inserted: int = 0
    updated: int = 0
    skipped_pseudo: int = 0
    skipped_foreign: int = 0
    skipped_unknown_account: int = 0
    assets_created: list[str] = field(default_factory=list)
    liabilities_created: list[str] = field(default_factory=list)
    assets_touched: set[str] = field(default_factory=set)
    liabilities_touched: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)

    @property
    def written(self) -> int:
        return self.inserted + self.updated


@dataclass
class BalancesImportSummary:
    """Aggregate across all files in one ``ingest()`` call."""

    files: list[BalancesFileReport] = field(default_factory=list)
    inserted: int = 0
    updated: int = 0

    @property
    def written(self) -> int:
        return self.inserted + self.updated

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


class MonarchBalancesImporter:
    """Stateful helper that writes balance snapshots to the database."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._account_cache: dict[str, Optional[ResolvedAccount]] = {}

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def ingest(self, files: Iterable[tuple[str, str]]) -> BalancesImportSummary:
        summary = BalancesImportSummary()
        for filename, content in files:
            report = self._ingest_file(filename, content)
            summary.files.append(report)
            summary.inserted += report.inserted
            summary.updated += report.updated
        return summary

    # ------------------------------------------------------------------
    # Per-file pipeline
    # ------------------------------------------------------------------

    def _ingest_file(self, filename: str, content: str) -> BalancesFileReport:
        report = BalancesFileReport(filename=filename)
        parsed: BalancesParseResult = parse_monarch_balances_csv(content)
        report.header_ok = parsed.header_ok
        report.warnings.extend(parsed.warnings)
        report.skipped_pseudo = parsed.skipped_pseudo
        report.skipped_foreign = parsed.skipped_foreign
        report.skipped_unknown_account = parsed.skipped_unknown
        report.rows_seen = (
            parsed.kept
            + parsed.skipped_pseudo
            + parsed.skipped_foreign
            + parsed.skipped_unknown
        )

        if not parsed.header_ok:
            return report

        for row in parsed.rows:
            self._ingest_row(row, report)

        return report

    def _ingest_row(self, row: BalanceRow, report: BalancesFileReport) -> None:
        resolved = self._resolve_cached(row)
        if resolved is None:
            report.skipped_unknown_account += 1
            return

        if resolved.created:
            if resolved.asset is not None and resolved.asset.name not in report.assets_created:
                report.assets_created.append(resolved.asset.name)
            if resolved.liability is not None and resolved.liability.name not in report.liabilities_created:
                report.liabilities_created.append(resolved.liability.name)
            if resolved.note:
                report.warnings.append(f"Account '{row.account_label}': {resolved.note}")

        if resolved.asset is not None:
            report.assets_touched.add(resolved.asset.name)
            self._upsert_asset(resolved.asset.id, row, report)
        elif resolved.liability is not None:
            report.liabilities_touched.add(resolved.liability.name)
            self._upsert_liability(resolved.liability.id, row, report)

    # ------------------------------------------------------------------
    # Upserts
    # ------------------------------------------------------------------

    def _upsert_asset(
        self,
        asset_id: int,
        row: BalanceRow,
        report: BalancesFileReport,
    ) -> None:
        currency = row.currency if row.currency in {"CAD", "USD"} else "CAD"
        existing = self.db.execute(
            select(AccountBalanceHistory).where(
                AccountBalanceHistory.asset_id == asset_id,
                AccountBalanceHistory.as_of_date == row.as_of,
                AccountBalanceHistory.currency == currency,
            )
        ).scalar_one_or_none()

        if existing is not None:
            # Only count as "updated" if the value actually changed — keeps
            # re-imports of the same file from inflating counters.
            if existing.balance != row.balance:
                existing.balance = row.balance
                existing.source = SOURCE
                report.updated += 1
            return

        self.db.add(
            AccountBalanceHistory(
                asset_id=asset_id,
                as_of_date=row.as_of,
                balance=row.balance,
                currency=currency,
                source=SOURCE,
            )
        )
        self.db.flush()
        report.inserted += 1

    def _upsert_liability(
        self,
        liability_id: int,
        row: BalanceRow,
        report: BalancesFileReport,
    ) -> None:
        # Monarch reports liabilities as negative; flip to positive so
        # downstream "amount owed" math stays consistent with the WS
        # importer.
        owed = abs(row.balance)
        recorded_at = datetime.combine(row.as_of, time.min, tzinfo=timezone.utc)

        # LiabilityBalanceHistory has no unique constraint, so scan for
        # an existing row on the same calendar day. This is O(n) per
        # liability per file but n is small (~weekly snapshots) and the
        # cost stays bounded.
        existing_rows = (
            self.db.execute(
                select(LiabilityBalanceHistory).where(
                    LiabilityBalanceHistory.liability_id == liability_id,
                )
            )
            .scalars()
            .all()
        )
        day_exists = False
        # Compare on calendar date only — SQLite drops tzinfo on
        # readback, which would otherwise raise
        # ``can't compare offset-naive and offset-aware datetimes``.
        latest_known_date = None
        for existing in existing_rows:
            if existing.recorded_at is None:
                continue
            existing_date = existing.recorded_at.date()
            if latest_known_date is None or existing_date > latest_known_date:
                latest_known_date = existing_date
            if existing_date == row.as_of:
                day_exists = True
                if existing.balance != owed:
                    existing.balance = owed
                    report.updated += 1

        if not day_exists:
            self.db.add(
                LiabilityBalanceHistory(
                    liability_id=liability_id,
                    balance=owed,
                    recorded_at=recorded_at,
                    is_statement_balance=False,
                )
            )
            self.db.flush()
            report.inserted += 1

        # Mirror the WS importer: whenever we write a snapshot that's at
        # least as recent as what's on the ``liabilities`` row, sync the
        # denormalised ``current_balance`` + ``balance_updated_at`` so
        # the Accounts page (which reads from ``current_balance``)
        # reflects the newest Monarch number without a join.
        if latest_known_date is None or row.as_of >= latest_known_date:
            liab = self.db.get(Liability, liability_id)
            if liab is not None:
                liab.current_balance = owed
                liab.balance_updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_cached(self, row: BalanceRow) -> Optional[ResolvedAccount]:
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


# ---------------------------------------------------------------------------
# Convenience entry points
# ---------------------------------------------------------------------------


def ingest_balances(
    db: Session, files: Iterable[tuple[str, str]]
) -> BalancesImportSummary:
    """Single-call helper used by the API layer."""
    return MonarchBalancesImporter(db).ingest(files)


__all__ = [
    "BalancesFileReport",
    "BalancesImportSummary",
    "MonarchBalancesImporter",
    "SOURCE",
    "ingest_balances",
]
