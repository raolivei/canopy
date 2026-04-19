"""Parse Monarch Money *balances* CSV exports.

Monarch's "Download account balances" export is a flat 3-column CSV::

    Date,Balance,Account

One row = one end-of-day snapshot for one account. Because Monarch is
connected to all of a user's institutions, this file fills the big gap
in the Canopy importer pipeline: non-Wealthsimple accounts (RBC,
Scotiabank, credit cards, etc.) now ship with historical balance
snapshots, so the Accounts page and net-worth timeline stop showing
``$0`` for them.

Sign convention:

* Assets (chequing / savings / investment): Monarch reports a
  **positive** balance.
* Liabilities (credit cards, lines of credit, loans): Monarch reports
  a **negative** balance ("you owe $21,818" -> ``-21818.66``).

The parser preserves the raw sign; the importer is responsible for
flipping liability balances to a positive "amount owed".

Canopy is CAD + USD only. Any account labelled with a foreign-currency
prefix (``EUR account``, ``TRY account``, ``COP account``, ...) is
classified as ``FOREIGN`` and silently dropped, matching the
transactions parser's behaviour.
"""

from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from backend.services.monarch.parser import (
    AccountClass,
    _classify_account,
    _extract_last4,
    _infer_currency,
)

REQUIRED_COLUMNS = ["Date", "Balance", "Account"]

# Monarch never emits these as real balance rows, but future-proof the
# filter anyway — matches the transactions parser.
PSEUDO_ACCOUNTS = {"Transfer", "Income", "Uncategorized", ""}


@dataclass(frozen=True)
class BalanceRow:
    """One parsed balance snapshot."""

    as_of: date
    balance: Decimal
    account_label: str
    account_class: AccountClass
    currency: str
    account_last4: Optional[str]


@dataclass
class BalancesParseResult:
    rows: list[BalanceRow] = field(default_factory=list)
    header_ok: bool = False
    skipped_pseudo: int = 0
    skipped_foreign: int = 0
    skipped_unknown: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def kept(self) -> int:
        return len(self.rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_monarch_balances_filename(filename: str) -> bool:
    """Return True if the filename looks like a Monarch balances export.

    Monarch's default naming scheme is ``Balances_<timestamp>.csv``; we
    also accept the lowercase / hyphenated variants some users rename to
    before dropping the file.
    """
    base = os.path.basename(filename).lower()
    if not base.endswith(".csv"):
        return False
    return base.startswith("balances_") or base.startswith("balances-") or base.startswith("monarch-balances")


def looks_like_balances_header(first_line: str) -> bool:
    """Cheap content-based detection, used to auto-route uploads."""
    cols = [c.strip() for c in first_line.strip().split(",")]
    return cols[: len(REQUIRED_COLUMNS)] == REQUIRED_COLUMNS


def parse_monarch_balances_csv(text: str) -> BalancesParseResult:
    """Tokenise a Monarch balances CSV.

    The parser is forgiving about row-level issues (bad dates, blank
    amounts) — those rows are dropped with a warning rather than
    raising. A header mismatch is a hard failure (``header_ok=False``).
    """
    result = BalancesParseResult()
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        result.warnings.append("File is empty or header row is missing.")
        return result
    missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
    if missing:
        result.warnings.append(
            "Header is missing required column(s): " + ", ".join(missing)
        )
        return result
    result.header_ok = True

    for i, raw in enumerate(reader, start=2):  # line 1 is the header
        row = _normalise(raw, line_no=i, out=result)
        if row is None:
            continue
        if row.account_class == AccountClass.PSEUDO:
            result.skipped_pseudo += 1
            continue
        if row.account_class == AccountClass.FOREIGN:
            result.skipped_foreign += 1
            continue
        if row.account_class == AccountClass.UNKNOWN:
            result.skipped_unknown += 1
            result.warnings.append(
                f"Line {i}: account '{row.account_label}' did not match any "
                "known classifier; row skipped."
            )
            continue
        result.rows.append(row)

    return result


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _normalise(
    raw: dict[str, str],
    *,
    line_no: int,
    out: BalancesParseResult,
) -> Optional[BalanceRow]:
    date_str = (raw.get("Date") or "").strip()
    m = _DATE_RE.match(date_str)
    if not m:
        out.warnings.append(f"Line {line_no}: unparseable date '{date_str}'")
        return None
    try:
        as_of = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        out.warnings.append(f"Line {line_no}: invalid date '{date_str}'")
        return None

    amount_str = (raw.get("Balance") or "").strip()
    if not amount_str:
        out.warnings.append(f"Line {line_no}: empty balance")
        return None
    try:
        balance = Decimal(amount_str)
    except InvalidOperation:
        out.warnings.append(f"Line {line_no}: unparseable balance '{amount_str}'")
        return None

    account_label = (raw.get("Account") or "").strip()
    if account_label in PSEUDO_ACCOUNTS:
        account_class = AccountClass.PSEUDO
        currency = "CAD"
        last4 = None
    else:
        account_class = _classify_account(account_label)
        currency = _infer_currency(account_label)
        last4 = _extract_last4(account_label)

    return BalanceRow(
        as_of=as_of,
        balance=balance,
        account_label=account_label,
        account_class=account_class,
        currency=currency,
        account_last4=last4,
    )
