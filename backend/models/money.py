"""Pydantic field types for money values.

API responses compute in ``Decimal`` and serialize money as a JSON number
rounded to cents, so the frontend keeps working with plain numbers while the
backend never sums floats.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

from backend.services.calculation.money import quantize


def _money_to_float(value: Decimal) -> float:
    return float(quantize(value))


Money = Annotated[Decimal, PlainSerializer(_money_to_float, return_type=float, when_used="json")]
"""A ``Decimal`` that serializes to a 2-decimal JSON number."""
