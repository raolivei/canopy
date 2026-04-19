"""Parse Wealthsimple monthly-statement CSV filenames.

Wealthsimple emits one CSV per account per statement period. The filename
encodes the account label, a Wealthsimple account number, and the statement
period-start date. Example filenames seen in the wild:

- ``Chequing-monthly-statement-transactions-WK15SYK37CAD-2025-12-01.csv``
- ``credit-card-statement-transactions-2025-12-01.csv``
- ``Crypto-monthly-statement-transactions-H68611617CAD-2026-03-01.csv``
- ``Direct Indexing-monthly-statement-transactions-WZ0BM4C09CAD-2026-03-01.csv``
- ``Emerging 🇮🇳🇯🇵🇧🇷-monthly-statement-transactions-HQ7P9HR40CAD-2026-03-01.csv``
- ``FHSA-monthly-statement-transactions-WK2F1TR60CAD-2026-03-01.csv``
- ``Portfolio line of credit-monthly-statement-transactions-HQB2DBL08CAD-2026-03-01.csv``
- ``Retirement ⛱️-monthly-statement-transactions-W88119545CAD-2025-12-01.csv``
- ``TFSA Long-monthly-statement-transactions-W880772K2CAD-2025-12-01.csv``
- ``TFSA-monthly-statement-transactions-HQB2DBYK0CAD-2026-03-01.csv``

This module is Unicode-safe (labels contain emoji).
"""

from __future__ import annotations

import enum
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional


class AccountClass(str, enum.Enum):
    """High-level routing bucket for downstream writes."""

    INVESTMENT = "investment"
    CASH = "cash"
    DEBT = "debt"
    SKIP = "skip"


class WsAccountKind(str, enum.Enum):
    """Concrete Wealthsimple account kind.

    Values mirror the names we use when populating ``Asset.asset_type``
    or ``Liability.liability_type`` downstream (see :mod:`backend.db.models`).
    """

    CHEQUING = "chequing"
    TFSA = "tfsa"
    TFSA_LONG = "tfsa_long"
    FHSA = "fhsa"
    RRSP = "rrsp"
    EMERGING = "emerging"
    CRYPTO = "crypto"
    DIRECT_INDEXING = "direct_indexing"  # skipped - account closed
    CREDIT_CARD = "credit_card"
    LINE_OF_CREDIT = "line_of_credit"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WsFileMeta:
    """Result of parsing a Wealthsimple CSV filename."""

    filename: str
    account_label: str
    account_kind: WsAccountKind
    account_class: AccountClass
    account_number: Optional[str]
    statement_period_start: Optional[date]
    skip_reason: Optional[str] = None

    @property
    def is_skipped(self) -> bool:
        return self.account_class == AccountClass.SKIP


_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_ACCOUNT_NUMBER_RE = re.compile(r"([A-Z0-9]{8,})CAD", re.I)


def _extract_date(stem: str) -> Optional[date]:
    m = _DATE_RE.search(stem)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _extract_account_number(stem: str) -> Optional[str]:
    m = _ACCOUNT_NUMBER_RE.search(stem)
    if not m:
        return None
    return m.group(0)  # includes the CAD suffix, matching Wealthsimple's own ID


_PREFIX_MAP: list[tuple[str, WsAccountKind, AccountClass]] = [
    ("Chequing-", WsAccountKind.CHEQUING, AccountClass.CASH),
    ("credit-card-statement-", WsAccountKind.CREDIT_CARD, AccountClass.DEBT),
    ("Portfolio line of credit-", WsAccountKind.LINE_OF_CREDIT, AccountClass.DEBT),
    ("Direct Indexing-", WsAccountKind.DIRECT_INDEXING, AccountClass.SKIP),
    ("Crypto-", WsAccountKind.CRYPTO, AccountClass.INVESTMENT),
    ("FHSA-", WsAccountKind.FHSA, AccountClass.INVESTMENT),
    ("TFSA Long-", WsAccountKind.TFSA_LONG, AccountClass.INVESTMENT),
    ("TFSA-", WsAccountKind.TFSA, AccountClass.INVESTMENT),
    # Labels that start with a word plus optional emoji (Retirement ⛱️-, Emerging 🇮🇳🇯🇵🇧🇷-)
    ("Retirement ", WsAccountKind.RRSP, AccountClass.INVESTMENT),
    ("Emerging ", WsAccountKind.EMERGING, AccountClass.INVESTMENT),
]


def is_wealthsimple_filename(filename: str) -> bool:
    """Return True if the filename matches a known Wealthsimple monthly-statement
    pattern (prefix + ``-monthly-statement-``, or the credit-card variant).

    Useful for routing: files that look like Wealthsimple statements belong in
    the Wealthsimple importer, not the portfolio-review snapshot importer.
    """
    base = os.path.basename(filename)
    stem = base[:-4] if base.lower().endswith(".csv") else base
    if "monthly-statement-transactions" in stem:
        return True
    if stem.startswith("credit-card-statement-transactions"):
        return True
    for prefix, _kind, _cls in _PREFIX_MAP:
        if stem.startswith(prefix):
            return True
    return False


def parse_filename(filename: str) -> WsFileMeta:
    """Classify a Wealthsimple CSV filename.

    Unknown filenames are returned with ``account_kind=UNKNOWN`` and
    ``account_class=SKIP`` so the caller can surface a warning.
    """
    base = os.path.basename(filename)
    stem = base[:-4] if base.lower().endswith(".csv") else base

    statement_date = _extract_date(stem)
    account_number = _extract_account_number(stem)

    for prefix, kind, cls in _PREFIX_MAP:
        if stem.startswith(prefix):
            label = _label_from_stem(stem, prefix)
            skip_reason = None
            if cls == AccountClass.SKIP:
                skip_reason = f"{kind.value.replace('_', ' ').title()} account is not imported"
            return WsFileMeta(
                filename=base,
                account_label=label,
                account_kind=kind,
                account_class=cls,
                account_number=account_number,
                statement_period_start=statement_date,
                skip_reason=skip_reason,
            )

    return WsFileMeta(
        filename=base,
        account_label=stem,
        account_kind=WsAccountKind.UNKNOWN,
        account_class=AccountClass.SKIP,
        account_number=account_number,
        statement_period_start=statement_date,
        skip_reason="Unrecognized Wealthsimple filename pattern",
    )


def _label_from_stem(stem: str, prefix: str) -> str:
    """Return the human-facing account label.

    For a stem like ``Retirement ⛱️-monthly-statement-transactions-W88119545CAD-2025-12-01``
    with prefix ``Retirement ``, this returns ``Retirement ⛱️``.
    For ``credit-card-statement-transactions-2025-12-01`` the prefix is
    ``credit-card-statement-`` and the label we expose is ``Credit Card``.
    """
    # Strip the static "-monthly-statement-..." suffix or "-statement-..." suffix.
    # The label is everything up to the first occurrence of either.
    label_part = stem
    for marker in ("-monthly-statement-transactions-", "-statement-transactions-"):
        idx = stem.find(marker)
        if idx != -1:
            label_part = stem[:idx]
            break

    # If the prefix already captures the full word (e.g. "Chequing-"), the
    # label part equals the prefix minus the trailing dash.
    if prefix.endswith("-") and label_part == prefix[:-1]:
        return prefix[:-1]

    # Handle the compound credit-card prefix explicitly.
    if prefix == "credit-card-statement-":
        return "Credit Card"

    return label_part.strip()
