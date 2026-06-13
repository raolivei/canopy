"""Transaction rules engine for auto-categorization, tagging, and splitting.

Handles rule creation, evaluation, and application to transactions.
"""

import re
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.rule import (
    Rule,
    RuleCondition,
    RuleAction,
    RuleConditionField,
    RuleConditionOperator,
    RuleActionType,
)
from backend.db.models.transaction import Transaction


class RuleEvaluationError(Exception):
    """Raised when rule evaluation fails."""

    pass


class RuleService:
    """Service for managing and applying transaction rules."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_rule(
        self,
        name: str,
        description: Optional[str] = None,
        priority: int = 0,
        conditions: Optional[List[dict]] = None,
        actions: Optional[List[dict]] = None,
        is_active: bool = True,
    ) -> Rule:
        """Create a new rule with conditions and actions.

        Args:
            name: Rule name
            description: Optional description
            priority: Priority for rule execution (higher first)
            conditions: List of condition dicts with keys: field, operator, value
            actions: List of action dicts with keys: action_type, value, order
            is_active: Whether rule is active

        Returns:
            Created Rule object
        """
        rule = Rule(
            name=name,
            description=description,
            priority=priority,
            is_active=is_active,
        )

        # Add conditions
        if conditions:
            for idx, cond in enumerate(conditions):
                condition = RuleCondition(
                    field=cond["field"],
                    operator=cond["operator"],
                    value=cond["value"],
                    numeric_value=cond.get("numeric_value"),
                )
                rule.conditions.append(condition)

        # Add actions (sorted by order)
        if actions:
            for action_dict in sorted(actions, key=lambda x: x.get("order", 0)):
                action = RuleAction(
                    action_type=action_dict["action_type"],
                    value=action_dict["value"],
                    order=action_dict.get("order", 0),
                    split_config=action_dict.get("split_config"),
                )
                rule.actions.append(action)

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_matching_rules(self, transaction: Transaction) -> List[Rule]:
        """Get all active rules that match the transaction.

        Args:
            transaction: Transaction to evaluate

        Returns:
            List of matching Rule objects (sorted by priority, highest first)
        """
        stmt = select(Rule).where(Rule.is_active == True).order_by(Rule.priority.desc())
        rules = self.db.execute(stmt).scalars().all()

        matching_rules = []
        for rule in rules:
            if self._evaluate_rule(rule, transaction):
                matching_rules.append(rule)

        return matching_rules

    def apply_rules_to_transaction(self, transaction: Transaction) -> Transaction:
        """Apply matching rules to a single transaction, modifying it in place.

        Args:
            transaction: Transaction to modify

        Returns:
            Modified transaction
        """
        matching_rules = self.get_matching_rules(transaction)

        for rule in matching_rules:
            # Sort actions by order
            for action in sorted(rule.actions, key=lambda a: a.order):
                transaction = self._apply_action(transaction, action)

        return transaction

    def apply_rules_to_import(self, transactions: List[Transaction]) -> List[Transaction]:
        """Apply matching rules to a batch of transactions.

        Args:
            transactions: List of transactions to modify

        Returns:
            List of modified transactions
        """
        return [self.apply_rules_to_transaction(txn) for txn in transactions]

    def _evaluate_rule(self, rule: Rule, transaction: Transaction) -> bool:
        """Evaluate if a rule matches a transaction (AND logic - all conditions must match).

        Args:
            rule: Rule to evaluate
            transaction: Transaction to evaluate against

        Returns:
            True if all conditions match, False otherwise
        """
        if not rule.conditions:
            return True  # No conditions = always match

        for condition in rule.conditions:
            if not self._evaluate_condition(condition, transaction):
                return False

        return True

    def _evaluate_condition(self, condition: RuleCondition, transaction: Transaction) -> bool:
        """Evaluate a single condition against a transaction.

        Args:
            condition: Condition to evaluate
            transaction: Transaction to evaluate against

        Returns:
            True if condition matches, False otherwise
        """
        try:
            # Get the field value from transaction
            if condition.field == RuleConditionField.MERCHANT:
                field_value = transaction.merchant or ""
            elif condition.field == RuleConditionField.AMOUNT:
                field_value = transaction.amount
            elif condition.field == RuleConditionField.DESCRIPTION:
                field_value = transaction.description or ""
            elif condition.field == RuleConditionField.CATEGORY:
                field_value = transaction.category or ""
            elif condition.field == RuleConditionField.ACCOUNT:
                field_value = transaction.account or ""
            elif condition.field == RuleConditionField.ORIGINAL_STATEMENT:
                field_value = transaction.original_statement or ""
            elif condition.field == RuleConditionField.TAGS:
                field_value = transaction.tags or []
            else:
                raise RuleEvaluationError(f"Unknown field: {condition.field}")

            # Evaluate operator
            if condition.operator == RuleConditionOperator.EQUALS:
                return self._match_equals(field_value, condition.value)
            elif condition.operator == RuleConditionOperator.CONTAINS:
                return self._match_contains(field_value, condition.value)
            elif condition.operator == RuleConditionOperator.REGEX:
                return self._match_regex(field_value, condition.value)
            elif condition.operator == RuleConditionOperator.STARTS_WITH:
                return self._match_starts_with(field_value, condition.value)
            elif condition.operator == RuleConditionOperator.ENDS_WITH:
                return self._match_ends_with(field_value, condition.value)
            elif condition.operator == RuleConditionOperator.GREATER_THAN:
                return self._match_greater_than(field_value, condition.numeric_value)
            elif condition.operator == RuleConditionOperator.LESS_THAN:
                return self._match_less_than(field_value, condition.numeric_value)
            elif condition.operator == RuleConditionOperator.GREATER_EQUAL:
                return self._match_greater_equal(field_value, condition.numeric_value)
            elif condition.operator == RuleConditionOperator.LESS_EQUAL:
                return self._match_less_equal(field_value, condition.numeric_value)
            else:
                raise RuleEvaluationError(f"Unknown operator: {condition.operator}")

        except Exception as e:
            raise RuleEvaluationError(f"Error evaluating condition: {e}")

    @staticmethod
    def _match_equals(value, pattern: str) -> bool:
        """Match exact equality (case-insensitive for strings)."""
        if isinstance(value, (list, str)) and isinstance(pattern, str):
            if isinstance(value, list):
                return pattern.lower() in [v.lower() for v in value]
            return value.lower() == pattern.lower()
        return str(value).lower() == str(pattern).lower()

    @staticmethod
    def _match_contains(value, pattern: str) -> bool:
        """Match substring (case-insensitive)."""
        if isinstance(value, list):
            return any(pattern.lower() in str(v).lower() for v in value)
        return pattern.lower() in str(value).lower()

    @staticmethod
    def _match_regex(value, pattern: str) -> bool:
        """Match regex pattern."""
        try:
            if isinstance(value, list):
                return any(re.search(pattern, str(v), re.IGNORECASE) for v in value)
            return bool(re.search(pattern, str(value), re.IGNORECASE))
        except re.error as e:
            raise RuleEvaluationError(f"Invalid regex pattern: {e}")

    @staticmethod
    def _match_starts_with(value, pattern: str) -> bool:
        """Match string prefix (case-insensitive)."""
        if isinstance(value, list):
            return any(str(v).lower().startswith(pattern.lower()) for v in value)
        return str(value).lower().startswith(pattern.lower())

    @staticmethod
    def _match_ends_with(value, pattern: str) -> bool:
        """Match string suffix (case-insensitive)."""
        if isinstance(value, list):
            return any(str(v).lower().endswith(pattern.lower()) for v in value)
        return str(value).lower().endswith(pattern.lower())

    @staticmethod
    def _match_greater_than(value, threshold: Optional[Decimal]) -> bool:
        """Match numeric greater than."""
        if threshold is None:
            return False
        try:
            return Decimal(str(value)) > threshold
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _match_less_than(value, threshold: Optional[Decimal]) -> bool:
        """Match numeric less than."""
        if threshold is None:
            return False
        try:
            return Decimal(str(value)) < threshold
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _match_greater_equal(value, threshold: Optional[Decimal]) -> bool:
        """Match numeric greater than or equal."""
        if threshold is None:
            return False
        try:
            return Decimal(str(value)) >= threshold
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _match_less_equal(value, threshold: Optional[Decimal]) -> bool:
        """Match numeric less than or equal."""
        if threshold is None:
            return False
        try:
            return Decimal(str(value)) <= threshold
        except (ValueError, TypeError):
            return False

    def _apply_action(self, transaction: Transaction, action: RuleAction) -> Transaction:
        """Apply a single action to a transaction.

        Args:
            transaction: Transaction to modify
            action: Action to apply

        Returns:
            Modified transaction
        """
        if action.action_type == RuleActionType.SET_CATEGORY:
            transaction.category = action.value

        elif action.action_type == RuleActionType.ADD_TAG:
            if transaction.tags is None:
                transaction.tags = []
            if action.value not in transaction.tags:
                transaction.tags.append(action.value)

        elif action.action_type == RuleActionType.SPLIT:
            # Split action is handled at a higher level (creates multiple transactions)
            # For now, we mark it with a special tag so the caller can handle it
            if transaction.tags is None:
                transaction.tags = []
            if "split:pending" not in transaction.tags:
                transaction.tags.append("split:pending")
            # Store split config in notes for processing
            if action.split_config:
                split_note = f"Split config: {action.split_config}"
                if transaction.notes:
                    transaction.notes += f"\n{split_note}"
                else:
                    transaction.notes = split_note

        return transaction

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule and its conditions/actions.

        Args:
            rule_id: ID of rule to delete

        Returns:
            True if deleted, False if not found
        """
        rule = self.db.query(Rule).get(rule_id)
        if rule:
            self.db.delete(rule)
            self.db.commit()
            return True
        return False

    def update_rule(self, rule_id: int, **kwargs) -> Optional[Rule]:
        """Update rule properties.

        Args:
            rule_id: ID of rule to update
            **kwargs: Fields to update (name, description, priority, is_active)

        Returns:
            Updated rule or None if not found
        """
        rule = self.db.query(Rule).get(rule_id)
        if not rule:
            return None

        allowed_fields = {"name", "description", "priority", "is_active"}
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(rule, key, value)

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rule(self, rule_id: int) -> Optional[Rule]:
        """Get a rule by ID.

        Args:
            rule_id: ID of rule to retrieve

        Returns:
            Rule or None if not found
        """
        return self.db.query(Rule).get(rule_id)

    def list_rules(self, active_only: bool = True) -> List[Rule]:
        """List all rules.

        Args:
            active_only: If True, only return active rules

        Returns:
            List of Rule objects
        """
        query = self.db.query(Rule)
        if active_only:
            query = query.where(Rule.is_active == True)
        return query.order_by(Rule.priority.desc()).all()
