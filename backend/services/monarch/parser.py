"""Parse Monarch Money transaction CSV exports.

Monarch exports are flat CSVs with a fixed 8-column header::

    Date,Merchant,Category,Account,Original Statement,Notes,Amount,Tags

Rows carry both a cleaned-up ``Merchant`` and the bank's raw
``Original Statement``. Amounts are signed decimals (expenses negative,
income positive, credit-card payments positive in the card account and
negative in the funding account).

The parser's job is narrow: validate the header, normalise each row into
a :class:`MonarchRow`, classify the account (investment / cash / debt /
skip), infer currency from the account label (``"USD account (...2015)"``
-> ``USD``), and tag pseudo-accounts that Monarch uses internally
(``Transfer``, ``Income``, ``Uncategorized``).

No database I/O here: resolving an account label to a Canopy
:class:`Asset` / :class:`Liability` lives in ``accounts.py``, and writing
transactions lives in ``importer.py``.
"""

from __future__ import annotations

import csv
import enum
import io
import os
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

REQUIRED_COLUMNS = [
    "Date",
    "Merchant",
    "Category",
    "Account",
    "Original Statement",
    "Notes",
    "Amount",
    "Tags",
]

# Monarch pseudo-accounts that are not real accounts and must be skipped.
PSEUDO_ACCOUNTS = {"Transfer", "Income", "Uncategorized", ""}


class AccountClass(str, enum.Enum):
    """High-level routing bucket for Monarch accounts."""

    INVESTMENT = "investment"
    CASH = "cash"
    DEBT = "debt"
    FOREIGN = "foreign"  # non-CAD; skipped by default at import time
    PSEUDO = "pseudo"  # Monarch's internal Transfer/Income/Uncategorized
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MonarchRow:
    """One parsed row, normalised into typed fields."""

    occurred_on: date
    merchant: str
    category: str
    account_label: str
    original_statement: str
    notes: str
    amount: Decimal
    tags: tuple[str, ...]
    account_class: AccountClass
    currency: str
    account_last4: Optional[str]


@dataclass
class ParseResult:
    """Full parse result for one Monarch file."""

    rows: list[MonarchRow] = field(default_factory=list)
    header_ok: bool = False
    skipped_pseudo: int = 0
    skipped_foreign: int = 0
    unknown_amount_rows: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def kept(self) -> int:
        return len(self.rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_monarch_filename(filename: str) -> bool:
    """Return True if the file looks like a Monarch transaction export.

    Monarch's default export filenames look like
    ``monarch-transactions-<id>-<uuid>.csv``.
    """
    base = os.path.basename(filename).lower()
    if not base.endswith(".csv"):
        return False
    return base.startswith("monarch-transactions") or base.startswith("monarch_transactions")


def parse_monarch_csv(text: str) -> ParseResult:
    """Tokenise a Monarch CSV export.

    The parser is forgiving about row-level issues (bad dates, empty
    amounts) - those rows are dropped with a warning rather than raising.
    Header mismatch is a hard failure (``header_ok=False``).
    """
    result = ParseResult()
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        result.warnings.append("File is empty or header row is missing.")
        return result
    missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
    if missing:
        result.warnings.append("Header is missing required column(s): " + ", ".join(missing))
        return result
    result.header_ok = True

    for i, raw in enumerate(reader, start=2):  # line 1 is the header
        row = _normalise_row(raw, line_no=i, out=result)
        if row is None:
            continue
        if row.account_class == AccountClass.PSEUDO:
            result.skipped_pseudo += 1
            continue
        if row.account_class == AccountClass.FOREIGN:
            result.skipped_foreign += 1
            continue
        result.rows.append(row)

    return result


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
# "(...2003)", "(...DqRQ)", "(...-5g0)", "(....8120)"
_LAST4_RE = re.compile(r"\(\.\.\.\.?([A-Za-z0-9\-]+)\)$")

_FOREIGN_PREFIXES = (
    "USD ",
    "USA ",
    "EUR ",
    "JPY ",
    "GBP ",
    "BRL ",
    "TRY ",
    "Credit Card USA",
)


def _normalise_row(
    raw: dict[str, str],
    *,
    line_no: int,
    out: ParseResult,
) -> Optional[MonarchRow]:
    date_str = (raw.get("Date") or "").strip()
    m = _DATE_RE.match(date_str)
    if not m:
        out.warnings.append(f"Line {line_no}: unparseable date '{date_str}'")
        return None
    try:
        occurred_on = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        out.warnings.append(f"Line {line_no}: invalid date '{date_str}'")
        return None

    amount_str = (raw.get("Amount") or "").strip()
    try:
        amount = Decimal(amount_str) if amount_str else None
    except InvalidOperation:
        amount = None
    if amount is None:
        out.unknown_amount_rows += 1
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

    tags_raw = (raw.get("Tags") or "").strip()
    tags = tuple(t.strip() for t in tags_raw.split(",") if t.strip())

    return MonarchRow(
        occurred_on=occurred_on,
        merchant=(raw.get("Merchant") or "").strip(),
        category=(raw.get("Category") or "").strip(),
        account_label=account_label,
        original_statement=(raw.get("Original Statement") or "").strip(),
        notes=(raw.get("Notes") or "").strip(),
        amount=amount,
        tags=tags,
        account_class=account_class,
        currency=currency,
        account_last4=last4,
    )


def _classify_account(label: str) -> AccountClass:
    """Classify a Monarch account label into a routing bucket.

    Heuristic, in priority order:
      1. Foreign-currency prefixes (USD/EUR/JPY/TRY/USA) -> FOREIGN
      2. Credit-card / line-of-credit keywords -> DEBT
      3. Investment account keywords (TFSA, RRSP, FHSA, DPSP, MANAGED_,
         SELF_DIRECTED_, CRYPTO) -> INVESTMENT
      4. Chequing / Savings / "Day to Day" / "Find & Save" / CASH / CAD
         account -> CASH
      5. Otherwise -> UNKNOWN (importer will skip with a warning)
    """
    if label.startswith(_FOREIGN_PREFIXES):
        return AccountClass.FOREIGN
    lower = label.lower()

    if any(kw in lower for kw in ("credit card", "credit line", "mastercard", "visa")):
        return AccountClass.DEBT

    inv_markers = (
        "tfsa",
        "rrsp",
        "fhsa",
        "dpsp",
        "managed_",
        "self_directed_",
        "crypto",
        "individual",
    )
    if any(m in lower for m in inv_markers):
        return AccountClass.INVESTMENT

    cash_markers = (
        "chequing",
        "checking",
        "savings",
        "day to day",
        "find & save",
        "cash",
        "cad account",
        "eq bank",
    )
    if any(m in lower for m in cash_markers):
        return AccountClass.CASH

    return AccountClass.UNKNOWN


def _infer_currency(label: str) -> str:
    if label.startswith("USD ") or label.startswith("USA "):
        return "USD"
    if label.startswith("EUR "):
        return "EUR"
    if label.startswith("JPY "):
        return "JPY"
    if label.startswith("GBP "):
        return "GBP"
    if label.startswith("BRL "):
        return "BRL"
    if label.startswith("TRY "):
        return "TRY"
    if label.startswith("Credit Card USA"):
        return "USD"
    return "CAD"


def _extract_last4(label: str) -> Optional[str]:
    m = _LAST4_RE.search(label)
    if not m:
        return None
    last4 = m.group(1)
    return last4[-4:] if len(last4) >= 4 else last4
