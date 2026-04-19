"""Tests for the shared canonical/source hash helpers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.services.canonical_hash import (
    canonical_event_hash,
    entity_key_for_asset,
    entity_key_for_liability,
    source_event_hash,
)


def test_canonical_hash_is_deterministic_and_amount_quantised() -> None:
    a = canonical_event_hash("asset:7", date(2024, 4, 10), Decimal("42.00"))
    b = canonical_event_hash("asset:7", date(2024, 4, 10), Decimal("42"))  # same value
    c = canonical_event_hash("asset:7", date(2024, 4, 10), Decimal("42.001"))  # rounds
    assert a == b == c
    assert len(a) == 64


def test_canonical_hash_differs_on_entity_or_date_or_amount() -> None:
    base = canonical_event_hash("asset:7", date(2024, 4, 10), Decimal("42.00"))
    assert base != canonical_event_hash("asset:8", date(2024, 4, 10), Decimal("42.00"))
    assert base != canonical_event_hash("asset:7", date(2024, 4, 11), Decimal("42.00"))
    assert base != canonical_event_hash("asset:7", date(2024, 4, 10), Decimal("42.01"))


def test_entity_key_helpers() -> None:
    assert entity_key_for_asset(12) == "asset:12"
    assert entity_key_for_liability(3) == "liability:3"


def test_source_event_hash_changes_with_any_field() -> None:
    a = source_event_hash("ws", "acct-A", "2024-04-10", "42.00")
    b = source_event_hash("ws", "acct-B", "2024-04-10", "42.00")
    c = source_event_hash("monarch", "acct-A", "2024-04-10", "42.00")
    assert len({a, b, c}) == 3
