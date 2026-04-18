"""Row-level parsers for Wealthsimple CSV files.

Two concrete shapes exist:

**Shape A** (all non-credit accounts)::

    "date","transaction","description","amount","balance","currency"

**Shape B** (credit card only)::

    "transaction_date","post_date","type","details","amount","currency"
"""

from __future__ import annotations

import csv
import enum
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Iterator, Optional


class ShapeKind(str, enum.Enum):
    """Detected CSV shape."""

    SHAPE_A = "shape_a"  # date/transaction/description/amount/balance/currency
    SHAPE_B = "shape_b"  # transaction_date/post_date/type/details/amount/currency
    UNKNOWN = "unknown"


class RowKind(str, enum.Enum):
    """Canonical row kind, independent of CSV shape.

    Maps Wealthsimple transaction codes to a small, stable vocabulary
    that downstream importers dispatch on.
    """

    BUY = "buy"
    SELL = "sell"
    DIV = "dividend"
    FEE = "fee"
    TAX = "tax"
    INTEREST = "interest"
    CONTRIB = "contribution"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    SHARE_TRANSFER = "share_transfer"
    GIVEAWAY = "giveaway"
    # Credit card row kinds
    CC_PURCHASE = "cc_purchase"
    CC_REFUND = "cc_refund"
    CC_PAYMENT = "cc_payment"
    CC_FEE = "cc_fee"
    CC_INTEREST = "cc_interest"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParsedRow:
    """Normalized view of one Wealthsimple CSV row."""

    kind: RowKind
    occurred_on: date
    amount: Decimal
    currency: str
    description: str
    raw_code: str  # WS transaction code (shape A) or type (shape B)
    balance: Optional[Decimal] = None
    post_date: Optional[date] = None


# Shape-A code -> RowKind
_SHAPE_A_MAP: dict[str, RowKind] = {
    "BUY": RowKind.BUY,
    "SELL": RowKind.SELL,
    "DIV": RowKind.DIV,
    "FEE": RowKind.FEE,
    "NRT": RowKind.TAX,
    "INT": RowKind.INTEREST,
    "CONT": RowKind.CONTRIB,
    "AFT_IN": RowKind.DEPOSIT,
    "EFT": RowKind.DEPOSIT,
    "EFTOUT": RowKind.WITHDRAW,
    "WD": RowKind.WITHDRAW,
    "TRFIN": RowKind.TRANSFER_IN,
    "TRFOUT": RowKind.TRANSFER_OUT,
    "TRFOUTTF": RowKind.SHARE_TRANSFER,
    "GIVEAWAY": RowKind.GIVEAWAY,
}


def _dec(s: Optional[str]) -> Optional[Decimal]:
    if s is None:
        return None
    t = s.strip()
    if not t:
        return None
    try:
        return Decimal(t.replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


def detect_shape(header: list[str]) -> ShapeKind:
    """Identify the CSV shape from its header row."""
    norm = [h.strip().lower() for h in header]
    if {"date", "transaction", "description", "amount", "balance", "currency"}.issubset(set(norm)):
        return ShapeKind.SHAPE_A
    if {"transaction_date", "post_date", "type", "details", "amount", "currency"}.issubset(
        set(norm)
    ):
        return ShapeKind.SHAPE_B
    return ShapeKind.UNKNOWN


def iter_rows(content: str) -> Iterator[tuple[ShapeKind, list[str], dict[str, str]]]:
    """Yield ``(shape, header, row_dict)`` for every non-empty data row.

    Header rows inside a multi-section file (rare but possible when
    Wealthsimple exports mixed CAD/USD blocks) are detected and emit
    a *new* shape with the fresh header row context.
    """
    reader = csv.reader(io.StringIO(content))
    header: Optional[list[str]] = None
    shape = ShapeKind.UNKNOWN
    for raw in reader:
        if not any((cell or "").strip() for cell in raw):
            continue
        if header is None:
            header = [c.strip() for c in raw]
            shape = detect_shape(header)
            continue
        # Re-detect if this row itself looks like a header (rare)
        if detect_shape([c.strip() for c in raw]) != ShapeKind.UNKNOWN:
            header = [c.strip() for c in raw]
            shape = detect_shape(header)
            continue
        if shape == ShapeKind.UNKNOWN:
            continue
        # Align row length with header; pad/truncate defensively
        cells = list(raw) + [""] * max(0, len(header) - len(raw))
        cells = cells[: len(header)]
        row_dict = {header[i]: (cells[i] or "").strip() for i in range(len(header))}
        yield shape, header, row_dict


def parse_shape_a(row: dict[str, str]) -> Optional[ParsedRow]:
    code = (row.get("transaction") or "").strip().upper()
    occurred = _date(row.get("date"))
    amount = _dec(row.get("amount"))
    if occurred is None or amount is None:
        return None
    kind = _SHAPE_A_MAP.get(code, RowKind.UNKNOWN)
    balance = _dec(row.get("balance"))
    currency = (row.get("currency") or "CAD").strip() or "CAD"
    return ParsedRow(
        kind=kind,
        occurred_on=occurred,
        amount=amount,
        currency=currency,
        description=(row.get("description") or "").strip(),
        raw_code=code,
        balance=balance,
    )


def parse_shape_b(row: dict[str, str]) -> Optional[ParsedRow]:
    """Normalize a credit-card row.

    Sign convention out of Wealthsimple: **purchases are positive, refunds
    negative** (i.e. "amount owed" delta). We keep that convention so that
    summing the amount column directly gives the statement balance delta.
    """
    occurred = _date(row.get("transaction_date"))
    post = _date(row.get("post_date"))
    amount = _dec(row.get("amount"))
    if occurred is None or amount is None:
        return None
    raw_type = (row.get("type") or "").strip()
    lowered = raw_type.lower()
    if "purchase" in lowered:
        kind = RowKind.CC_PURCHASE
    elif "refund" in lowered:
        kind = RowKind.CC_REFUND
    elif "payment" in lowered:
        kind = RowKind.CC_PAYMENT
    elif "interest" in lowered:
        kind = RowKind.CC_INTEREST
    elif "fee" in lowered:
        kind = RowKind.CC_FEE
    else:
        kind = RowKind.UNKNOWN
    currency = (row.get("currency") or "CAD").strip() or "CAD"
    return ParsedRow(
        kind=kind,
        occurred_on=occurred,
        amount=amount,
        currency=currency,
        description=(row.get("details") or "").strip(),
        raw_code=raw_type,
        post_date=post,
    )


def parse_rows(content: str) -> Iterable[ParsedRow]:
    """Convenience helper: parse a full file's rows in one pass."""
    for shape, _header, row_dict in iter_rows(content):
        if shape == ShapeKind.SHAPE_A:
            parsed = parse_shape_a(row_dict)
        elif shape == ShapeKind.SHAPE_B:
            parsed = parse_shape_b(row_dict)
        else:
            parsed = None
        if parsed is not None:
            yield parsed
