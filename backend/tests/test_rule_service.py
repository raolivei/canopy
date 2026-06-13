"""Tests for transaction rules engine."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.db.base import Base
from backend.db.models.transaction import Transaction, TransactionType
from backend.db.models.rule import (
    Rule,
    RuleConditionField,
    RuleConditionOperator,
    RuleActionType,
)
from backend.services.rule_service import RuleService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def rule_service(db_session):
    """Create rule service instance."""
    return RuleService(db_session)


@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    return Transaction(
        description="Amazon Purchase",
        amount=Decimal("49.99"),
        currency="CAD",
        type=TransactionType.EXPENSE,
        date=datetime.now(timezone.utc),
        merchant="Amazon",
        original_statement="AMAZON.CA SEATTLE WA",
        account="Chequing",
        category=None,
        tags=[],
    )


class TestRuleCreation:
    """Test rule creation."""

    def test_create_rule_with_conditions(self, rule_service, db_session):
        """Test creating a rule with conditions."""
        rule = rule_service.create_rule(
            name="Amazon Rule",
            description="Auto-categorize Amazon purchases",
            priority=10,
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                }
            ],
            actions=[
                {
                    "action_type": "set_category",
                    "value": "Shopping",
                    "order": 0,
                }
            ],
        )

        assert rule.name == "Amazon Rule"
        assert rule.priority == 10
        assert rule.is_active is True
        assert len(rule.conditions) == 1
        assert len(rule.actions) == 1

    def test_create_rule_minimal(self, rule_service):
        """Test creating minimal rule."""
        rule = rule_service.create_rule(name="Test Rule")
        assert rule.name == "Test Rule"
        assert rule.priority == 0
        assert len(rule.conditions) == 0
        assert len(rule.actions) == 0


class TestRuleEvaluation:
    """Test rule condition evaluation."""

    def test_merchant_equals(self, rule_service, sample_transaction):
        """Test merchant equals condition."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_merchant_contains(self, rule_service, sample_transaction):
        """Test merchant contains condition."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "contains",
                    "value": "zon",
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_merchant_starts_with(self, rule_service, sample_transaction):
        """Test merchant starts_with condition."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "starts_with",
                    "value": "Amazon",
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_amount_greater_than(self, rule_service, sample_transaction):
        """Test amount greater_than condition."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "amount",
                    "operator": "greater_than",
                    "numeric_value": Decimal("40.00"),
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_amount_less_than(self, rule_service, sample_transaction):
        """Test amount less_than condition."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "amount",
                    "operator": "less_than",
                    "numeric_value": Decimal("100.00"),
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_condition_not_match(self, rule_service, sample_transaction):
        """Test condition that doesn't match."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Costco",
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is False

    def test_multiple_conditions_all_match(self, rule_service, sample_transaction):
        """Test multiple conditions (AND logic)."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                },
                {
                    "field": "amount",
                    "operator": "greater_than",
                    "numeric_value": Decimal("40.00"),
                },
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_multiple_conditions_one_fails(self, rule_service, sample_transaction):
        """Test multiple conditions where one fails."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                },
                {
                    "field": "amount",
                    "operator": "greater_than",
                    "numeric_value": Decimal("100.00"),
                },
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is False


class TestRuleActions:
    """Test rule action application."""

    def test_set_category_action(self, rule_service, sample_transaction):
        """Test set_category action."""
        rule = rule_service.create_rule(
            name="Test",
            actions=[
                {
                    "action_type": "set_category",
                    "value": "Shopping",
                    "order": 0,
                }
            ],
        )

        modified = rule_service._apply_action(sample_transaction, rule.actions[0])
        assert modified.category == "Shopping"

    def test_add_tag_action(self, rule_service, sample_transaction):
        """Test add_tag action."""
        rule = rule_service.create_rule(
            name="Test",
            actions=[
                {
                    "action_type": "add_tag",
                    "value": "online",
                    "order": 0,
                }
            ],
        )

        modified = rule_service._apply_action(sample_transaction, rule.actions[0])
        assert "online" in modified.tags

    def test_add_tag_no_duplicate(self, rule_service, sample_transaction):
        """Test that add_tag doesn't create duplicates."""
        sample_transaction.tags = ["online"]
        rule = rule_service.create_rule(
            name="Test",
            actions=[
                {
                    "action_type": "add_tag",
                    "value": "online",
                    "order": 0,
                }
            ],
        )

        modified = rule_service._apply_action(sample_transaction, rule.actions[0])
        assert modified.tags.count("online") == 1

    def test_multiple_actions_in_order(self, rule_service, sample_transaction):
        """Test applying multiple actions in order."""
        rule = rule_service.create_rule(
            name="Test",
            actions=[
                {
                    "action_type": "set_category",
                    "value": "Shopping",
                    "order": 0,
                },
                {
                    "action_type": "add_tag",
                    "value": "online",
                    "order": 1,
                },
            ],
        )

        # Apply actions in order
        result = sample_transaction
        for action in sorted(rule.actions, key=lambda a: a.order):
            result = rule_service._apply_action(result, action)

        assert result.category == "Shopping"
        assert "online" in result.tags


class TestRuleMatching:
    """Test rule matching and application."""

    def test_get_matching_rules(self, rule_service, sample_transaction):
        """Test getting matching rules."""
        rule1 = rule_service.create_rule(
            name="Amazon Rule",
            priority=10,
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                }
            ],
        )

        rule2 = rule_service.create_rule(
            name="Online Rule",
            priority=5,
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Costco",
                }
            ],
        )

        matching = rule_service.get_matching_rules(sample_transaction)
        assert len(matching) == 1
        assert matching[0].id == rule1.id

    def test_rule_priority_order(self, rule_service, sample_transaction):
        """Test that matching rules are ordered by priority."""
        rule1 = rule_service.create_rule(
            name="Low Priority",
            priority=5,
            conditions=[
                {
                    "field": "merchant",
                    "operator": "contains",
                    "value": "ama",
                }
            ],
        )

        rule2 = rule_service.create_rule(
            name="High Priority",
            priority=20,
            conditions=[
                {
                    "field": "merchant",
                    "operator": "contains",
                    "value": "ama",
                }
            ],
        )

        matching = rule_service.get_matching_rules(sample_transaction)
        assert matching[0].priority == 20
        assert matching[1].priority == 5

    def test_apply_rules_to_transaction(self, rule_service, sample_transaction):
        """Test applying rules to a transaction."""
        rule_service.create_rule(
            name="Amazon Rule",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                }
            ],
            actions=[
                {
                    "action_type": "set_category",
                    "value": "Shopping",
                    "order": 0,
                },
                {
                    "action_type": "add_tag",
                    "value": "online",
                    "order": 1,
                },
            ],
        )

        result = rule_service.apply_rules_to_transaction(sample_transaction)
        assert result.category == "Shopping"
        assert "online" in result.tags

    def test_apply_rules_to_import(self, rule_service, sample_transaction):
        """Test applying rules to multiple transactions."""
        txn2 = Transaction(
            description="Costco Purchase",
            amount=Decimal("150.00"),
            currency="CAD",
            type=TransactionType.EXPENSE,
            date=datetime.now(timezone.utc),
            merchant="Costco",
            account="Chequing",
        )

        rule_service.create_rule(
            name="Amazon Rule",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "equals",
                    "value": "Amazon",
                }
            ],
            actions=[
                {
                    "action_type": "set_category",
                    "value": "Shopping",
                    "order": 0,
                }
            ],
        )

        result = rule_service.apply_rules_to_import([sample_transaction, txn2])
        assert result[0].category == "Shopping"
        assert result[1].category is None


class TestRuleManagement:
    """Test rule CRUD operations."""

    def test_update_rule(self, rule_service):
        """Test updating rule properties."""
        rule = rule_service.create_rule(
            name="Original", priority=5, is_active=True
        )

        updated = rule_service.update_rule(
            rule.id, name="Updated", priority=20, is_active=False
        )

        assert updated.name == "Updated"
        assert updated.priority == 20
        assert updated.is_active is False

    def test_delete_rule(self, rule_service):
        """Test deleting a rule."""
        rule = rule_service.create_rule(name="To Delete")
        assert rule_service.delete_rule(rule.id) is True
        assert rule_service.get_rule(rule.id) is None

    def test_get_rule(self, rule_service):
        """Test retrieving a rule by ID."""
        rule = rule_service.create_rule(name="Test Rule")
        retrieved = rule_service.get_rule(rule.id)
        assert retrieved.name == "Test Rule"

    def test_list_rules(self, rule_service):
        """Test listing all rules."""
        rule1 = rule_service.create_rule(name="Active", is_active=True)
        rule2 = rule_service.create_rule(name="Inactive", is_active=False)

        all_rules = rule_service.list_rules(active_only=False)
        active_rules = rule_service.list_rules(active_only=True)

        assert len(all_rules) == 2
        assert len(active_rules) == 1
        assert active_rules[0].id == rule1.id


class TestRegexMatching:
    """Test regex pattern matching in conditions."""

    def test_regex_merchant(self, rule_service, sample_transaction):
        """Test regex matching on merchant field."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "regex",
                    "value": r"^amazon.*$",
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is True

    def test_regex_no_match(self, rule_service, sample_transaction):
        """Test regex that doesn't match."""
        rule = rule_service.create_rule(
            name="Test",
            conditions=[
                {
                    "field": "merchant",
                    "operator": "regex",
                    "value": r"^costco.*$",
                }
            ],
        )
        assert rule_service._evaluate_rule(rule, sample_transaction) is False
