"""Flow classification by transaction type."""

from decimal import Decimal

import pytest

from backend.services.calculation import EXCLUDED_TYPES, FLOW_TYPES, classify


@pytest.mark.parametrize(
    "tx_type, amount, expected",
    [
        ("income", "5000.00", ("income", Decimal("5000.00"))),
        ("income", "-5000.00", ("income", Decimal("5000.00"))),  # sign ignored
        ("expense", "-150.25", ("expense", Decimal("150.25"))),
        ("expense", "150.25", ("expense", Decimal("150.25"))),  # CSV stores abs
        ("EXPENSE ", 10, ("expense", Decimal("10"))),
    ],
)
def test_classify_uses_type_and_absolute_magnitude(tx_type, amount, expected):
    assert classify(tx_type, amount) == expected


@pytest.mark.parametrize("tx_type", sorted(EXCLUDED_TYPES) + ["dividend", None, ""])
def test_excluded_and_unknown_types_have_no_flow_kind(tx_type):
    kind, magnitude = classify(tx_type, "-42.00")
    assert kind is None
    assert magnitude == Decimal("42.00")


def test_flow_types_never_overlap_excluded_types():
    assert not FLOW_TYPES & EXCLUDED_TYPES
