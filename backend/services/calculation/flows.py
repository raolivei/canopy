"""Classify a transaction into an income or expense flow.

``Transaction.type`` is the authority. The sign of ``amount`` is **not**: the
Monarch importer keeps signed amounts while the CSV importer stores absolute
values, so consumers always work with ``abs(amount)`` and the type.

Known limitations (data model, not this module):

* No refund flag. A refund imported from Monarch arrives as a positive amount
  typed ``income``; from CSV as an ``expense`` with an absolute amount. Both
  are reported as-is.
* No hidden/pending/split markers. Every stored row counts once.

These are tracked under the transaction review work package (W2).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

FlowKind = Literal["income", "expense"]

INCOME_TYPES: frozenset[str] = frozenset({"income"})
EXPENSE_TYPES: frozenset[str] = frozenset({"expense"})
# Movements between the user's own accounts and investment trades are not
# cash flow; they are excluded, never counted as income or spending.
EXCLUDED_TYPES: frozenset[str] = frozenset({"transfer", "buy", "sell"})
FLOW_TYPES: frozenset[str] = INCOME_TYPES | EXPENSE_TYPES


def classify(tx_type: str | None, amount: Decimal | int | float | str) -> tuple[FlowKind | None, Decimal]:
    """Return ``(kind, magnitude)`` for a transaction.

    ``kind`` is ``None`` for excluded or unknown types. ``magnitude`` is always
    the absolute value as a ``Decimal``.
    """
    magnitude = abs(Decimal(str(amount)))
    normalized = (tx_type or "").strip().lower()
    if normalized in INCOME_TYPES:
        return "income", magnitude
    if normalized in EXPENSE_TYPES:
        return "expense", magnitude
    return None, magnitude
