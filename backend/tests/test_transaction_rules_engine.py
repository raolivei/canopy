"""Tests for TransactionRulesEngine.

Coverage:
- apply_rules() with priority ordering
- evaluate_condition() for all operators
- Actions: set_category, add_tag, set_merchant
- stop_on_match behavior
- Edge cases: no rules, multiple matches, invalid regex
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.transaction import Transaction
from backend.db.models.transaction_rule import TransactionRule
from backend.services.transaction_rules_engine import RulesEngine


@pytest.fixture
def db() -> Session:
    """Provide in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


@pytest.fixture
def sample_transaction(db: Session) -> Transaction:
    """Sample transaction for testing."""
    tx = Transaction(
        description="Coffee at Starbucks",
        merchant="Starbucks",
        amount=Decimal("5.50"),
        currency="CAD",
        type="expense",
        date=datetime(2026, 6, 16, 10, 0, 0),
        category=None,
        tags=None,
    )
    db.add(tx)
    db.flush()
    return tx


def test_apply_rules_basic_match(db: Session, sample_transaction: Transaction) -> None:
    """Test basic rule application with merchant match."""
    rule = TransactionRule(
        name="Starbucks → Dining",
        priority=10,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "Dining"}]},
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(sample_transaction)

    assert len(actions) == 1
    assert actions[0]["action"] == "set_category"
    assert actions[0]["value"] == "Dining"
    assert sample_transaction.category == "Dining"


def test_apply_rules_priority_order(db: Session, sample_transaction: Transaction) -> None:
    """Test rules evaluated in priority order (highest first)."""
    rule_low = TransactionRule(
        name="Low priority",
        priority=5,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "Low"}]},
    )
    rule_high = TransactionRule(
        name="High priority",
        priority=20,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "High"}]},
    )
    db.add_all([rule_low, rule_high])
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(sample_transaction)

    # High priority rule applies first
    assert sample_transaction.category == "High"
    assert len(actions) == 2  # Both rules match


def test_apply_rules_stop_on_match(db: Session, sample_transaction: Transaction) -> None:
    """Test stop_on_match prevents further rule evaluation."""
    rule1 = TransactionRule(
        name="First rule",
        priority=20,
        active=True,
        stop_on_match=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "First"}]},
    )
    rule2 = TransactionRule(
        name="Second rule",
        priority=10,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "Second"}]},
    )
    db.add_all([rule1, rule2])
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(sample_transaction)

    # Only first rule applies
    assert len(actions) == 1
    assert sample_transaction.category == "First"


def test_string_operators(db: Session) -> None:
    """Test all string operators: contains, equals, starts_with, ends_with, regex."""
    engine = RulesEngine(db)

    tx = Transaction(
        description="Test",
        merchant="Starbucks Coffee",
        amount=Decimal("5.00"),
        currency="CAD",
        type="expense",
        date=datetime.now(),
    )

    # contains
    assert engine._evaluate_condition({"field": "merchant", "operator": "contains", "value": "star"}, tx)
    assert not engine._evaluate_condition({"field": "merchant", "operator": "contains", "value": "dunkin"}, tx)

    # equals
    assert engine._evaluate_condition({"field": "merchant", "operator": "equals", "value": "starbucks coffee"}, tx)
    assert not engine._evaluate_condition({"field": "merchant", "operator": "equals", "value": "starbucks"}, tx)

    # starts_with
    assert engine._evaluate_condition({"field": "merchant", "operator": "starts_with", "value": "star"}, tx)
    assert not engine._evaluate_condition({"field": "merchant", "operator": "starts_with", "value": "coffee"}, tx)

    # ends_with
    assert engine._evaluate_condition({"field": "merchant", "operator": "ends_with", "value": "coffee"}, tx)
    assert not engine._evaluate_condition({"field": "merchant", "operator": "ends_with", "value": "star"}, tx)

    # regex
    assert engine._evaluate_condition({"field": "merchant", "operator": "regex", "value": r"^Star.*Coffee$"}, tx)
    assert not engine._evaluate_condition({"field": "merchant", "operator": "regex", "value": r"^\d+$"}, tx)


def test_numeric_operators(db: Session) -> None:
    """Test numeric operators: gt, lt, gte, lte, equals."""
    engine = RulesEngine(db)

    tx = Transaction(
        description="Test",
        merchant="Test",
        amount=Decimal("100.00"),
        currency="CAD",
        type="expense",
        date=datetime.now(),
    )

    # gt
    assert engine._evaluate_condition({"field": "amount", "operator": "gt", "value": "99.99"}, tx)
    assert not engine._evaluate_condition({"field": "amount", "operator": "gt", "value": "100.00"}, tx)

    # lt
    assert engine._evaluate_condition({"field": "amount", "operator": "lt", "value": "100.01"}, tx)
    assert not engine._evaluate_condition({"field": "amount", "operator": "lt", "value": "100.00"}, tx)

    # gte
    assert engine._evaluate_condition({"field": "amount", "operator": "gte", "value": "100.00"}, tx)
    assert engine._evaluate_condition({"field": "amount", "operator": "gte", "value": "99.99"}, tx)

    # lte
    assert engine._evaluate_condition({"field": "amount", "operator": "lte", "value": "100.00"}, tx)
    assert engine._evaluate_condition({"field": "amount", "operator": "lte", "value": "100.01"}, tx)

    # equals
    assert engine._evaluate_condition({"field": "amount", "operator": "equals", "value": "100.00"}, tx)


def test_all_actions(db: Session, sample_transaction: Transaction) -> None:
    """Test all action types: set_category, add_tag, set_merchant."""
    rule = TransactionRule(
        name="Multi-action rule",
        priority=10,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={
            "actions": [
                {"type": "set_category", "value": "Dining"},
                {"type": "add_tag", "value": "coffee"},
                {"type": "set_merchant", "value": "Starbucks"},
            ]
        },
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(sample_transaction)

    assert len(actions) == 3
    assert sample_transaction.category == "Dining"
    assert "coffee" in sample_transaction.tags
    assert sample_transaction.merchant == "Starbucks"


def test_add_tag_no_duplicates(db: Session, sample_transaction: Transaction) -> None:
    """Test add_tag doesn't create duplicates."""
    sample_transaction.tags = ["existing"]

    rule = TransactionRule(
        name="Tag rule",
        priority=10,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "add_tag", "value": "existing"}]},
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(sample_transaction)

    # No action applied since tag already exists
    assert len(actions) == 0
    assert sample_transaction.tags == ["existing"]


def test_no_active_rules(db: Session, sample_transaction: Transaction) -> None:
    """Test no actions when no active rules."""
    rule = TransactionRule(
        name="Inactive rule",
        priority=10,
        active=False,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "Dining"}]},
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(sample_transaction)

    assert len(actions) == 0
    assert sample_transaction.category is None


def test_invalid_regex_returns_false(db: Session) -> None:
    """Test invalid regex pattern returns False instead of crashing."""
    engine = RulesEngine(db)

    tx = Transaction(
        description="Test",
        merchant="Starbucks",
        amount=Decimal("5.00"),
        currency="CAD",
        type="expense",
        date=datetime.now(),
    )

    # Invalid regex pattern
    result = engine._evaluate_condition({"field": "merchant", "operator": "regex", "value": "["}, tx)
    assert result is False


def test_rule_statistics_updated(db: Session, sample_transaction: Transaction) -> None:
    """Test rule match_count and last_matched_at are updated."""
    rule = TransactionRule(
        name="Test rule",
        priority=10,
        active=True,
        match_count=0,
        last_matched_at=None,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "Dining"}]},
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    engine.apply_rules(sample_transaction)

    db.refresh(rule)
    assert rule.match_count == 1
    assert rule.last_matched_at is not None


def test_test_rule_method(db: Session, sample_transaction: Transaction) -> None:
    """Test test_rule() returns match info without applying changes."""
    rule = TransactionRule(
        name="Test rule",
        priority=10,
        active=True,
        conditions={"conditions": [{"field": "merchant", "operator": "contains", "value": "Starbucks"}]},
        actions={"actions": [{"type": "set_category", "value": "Dining"}]},
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    result = engine.test_rule(rule.id, sample_transaction)

    assert result["matched"] is True
    assert result["rule_id"] == rule.id
    assert result["rule_name"] == "Test rule"
    assert "actions" in result
    # Transaction not modified
    assert sample_transaction.category is None


def test_multiple_conditions_all_must_match(db: Session) -> None:
    """Test multiple conditions use AND logic."""
    tx = Transaction(
        description="Test",
        merchant="Starbucks",
        amount=Decimal("1500.00"),
        currency="CAD",
        type="expense",
        date=datetime.now(),
    )
    db.add(tx)
    db.flush()

    rule = TransactionRule(
        name="Multi-condition rule",
        priority=10,
        active=True,
        conditions={
            "conditions": [
                {"field": "merchant", "operator": "contains", "value": "Starbucks"},
                {"field": "amount", "operator": "gt", "value": "1000"},
            ]
        },
        actions={"actions": [{"type": "add_tag", "value": "large-purchase"}]},
    )
    db.add(rule)
    db.flush()

    engine = RulesEngine(db)
    actions = engine.apply_rules(tx)

    assert len(actions) == 1
    assert "large-purchase" in tx.tags


def test_condition_with_none_field_returns_false(db: Session) -> None:
    """Test condition returns False when transaction field is None."""
    engine = RulesEngine(db)

    tx = Transaction(
        description="Test",
        merchant=None,
        amount=Decimal("5.00"),
        currency="CAD",
        type="expense",
        date=datetime.now(),
    )

    result = engine._evaluate_condition({"field": "merchant", "operator": "contains", "value": "test"}, tx)
    assert result is False
