"""Transaction rules engine for automatic categorization and tagging.

Canopy - Personal Finance Platform
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction
from backend.db.models.transaction_rule import TransactionRule


class RulesEngine:
    """Engine for applying transaction rules to transactions."""

    # Supported operators for different field types
    STRING_OPERATORS = {"contains", "equals", "starts_with", "ends_with", "regex"}
    NUMERIC_OPERATORS = {"gt", "lt", "gte", "lte", "equals"}
    ARRAY_OPERATORS = {"in", "not_in"}

    def __init__(self, db: Session):
        """Initialize rules engine.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def apply_rules(self, transaction: Transaction) -> list[dict[str, Any]]:
        """Apply all active rules to a transaction.

        Rules are evaluated in priority order (highest first).
        If a rule matches and has stop_on_match=True, no further rules are evaluated.

        Args:
            transaction: Transaction to apply rules to

        Returns:
            List of applied actions with rule info
        """
        # Get all active rules ordered by priority (highest first)
        query = select(TransactionRule).where(TransactionRule.active == True).order_by(TransactionRule.priority.desc())

        rules = self.db.execute(query).scalars().all()

        applied_actions = []

        for rule in rules:
            if self._evaluate_rule(rule, transaction):
                # Apply actions
                actions = self._apply_actions(rule, transaction)
                applied_actions.extend(actions)

                # Update rule statistics
                rule.match_count += 1
                rule.last_matched_at = datetime.now()
                self.db.commit()

                # Stop if rule has stop_on_match flag
                if rule.stop_on_match:
                    break

        return applied_actions

    def test_rule(self, rule_id: int, transaction: Transaction) -> dict[str, Any]:
        """Test a rule against a transaction without applying changes.

        Args:
            rule_id: ID of rule to test
            transaction: Transaction to test against

        Returns:
            Dictionary with match result and would-be actions
        """
        rule = self.db.get(TransactionRule, rule_id)
        if not rule:
            return {"matched": False, "error": "Rule not found"}

        matched = self._evaluate_rule(rule, transaction)

        result = {
            "matched": matched,
            "rule_id": rule.id,
            "rule_name": rule.name,
        }

        if matched:
            # Show what actions would be applied (without actually applying them)
            result["actions"] = rule.actions

        return result

    def _evaluate_rule(self, rule: TransactionRule, transaction: Transaction) -> bool:
        """Evaluate if a rule's conditions match a transaction.

        Args:
            rule: Transaction rule to evaluate
            transaction: Transaction to evaluate against

        Returns:
            True if all conditions match, False otherwise
        """
        conditions = rule.conditions.get("conditions", [])

        if not conditions:
            return False

        # All conditions must match (AND logic)
        for condition in conditions:
            if not self._evaluate_condition(condition, transaction):
                return False

        return True

    def _evaluate_condition(self, condition: dict[str, Any], transaction: Transaction) -> bool:
        """Evaluate a single condition against a transaction.

        Args:
            condition: Condition dictionary with field, operator, and value
            transaction: Transaction to evaluate against

        Returns:
            True if condition matches, False otherwise
        """
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not all([field, operator, value is not None]):
            return False

        # Get field value from transaction
        tx_value = getattr(transaction, field, None)

        if tx_value is None:
            return False

        # String operators
        if operator in self.STRING_OPERATORS:
            return self._evaluate_string_condition(str(tx_value), operator, str(value))

        # Numeric operators
        if operator in self.NUMERIC_OPERATORS:
            return self._evaluate_numeric_condition(tx_value, operator, value)

        # Array operators
        if operator in self.ARRAY_OPERATORS:
            return self._evaluate_array_condition(tx_value, operator, value)

        return False

    def _evaluate_string_condition(self, tx_value: str, operator: str, value: str) -> bool:
        """Evaluate string condition.

        Args:
            tx_value: Transaction field value
            operator: Comparison operator
            value: Target value

        Returns:
            True if condition matches
        """
        tx_value_lower = tx_value.lower()
        value_lower = value.lower()

        if operator == "contains":
            return value_lower in tx_value_lower
        elif operator == "equals":
            return tx_value_lower == value_lower
        elif operator == "starts_with":
            return tx_value_lower.startswith(value_lower)
        elif operator == "ends_with":
            return tx_value_lower.endswith(value_lower)
        elif operator == "regex":
            try:
                return bool(re.search(value, tx_value, re.IGNORECASE))
            except re.error:
                return False

        return False

    def _evaluate_numeric_condition(self, tx_value: Any, operator: str, value: Any) -> bool:
        """Evaluate numeric condition.

        Args:
            tx_value: Transaction field value
            operator: Comparison operator
            value: Target value

        Returns:
            True if condition matches
        """
        try:
            # Convert to Decimal for consistent comparison
            if isinstance(tx_value, Decimal):
                tx_num = tx_value
            else:
                tx_num = Decimal(str(tx_value))

            if isinstance(value, Decimal):
                target_num = value
            else:
                target_num = Decimal(str(value))

            if operator == "gt":
                return tx_num > target_num
            elif operator == "lt":
                return tx_num < target_num
            elif operator == "gte":
                return tx_num >= target_num
            elif operator == "lte":
                return tx_num <= target_num
            elif operator == "equals":
                return tx_num == target_num

        except (ValueError, TypeError, ArithmeticError):
            return False

        return False

    def _evaluate_array_condition(self, tx_value: Any, operator: str, value: Any) -> bool:
        """Evaluate array condition.

        Args:
            tx_value: Transaction field value
            operator: Comparison operator
            value: Target value(s)

        Returns:
            True if condition matches
        """
        if operator == "in":
            # Check if tx_value is in the list of values
            if isinstance(value, list):
                return tx_value in value
            return tx_value == value

        elif operator == "not_in":
            # Check if tx_value is NOT in the list of values
            if isinstance(value, list):
                return tx_value not in value
            return tx_value != value

        return False

    def _apply_actions(self, rule: TransactionRule, transaction: Transaction) -> list[dict[str, Any]]:
        """Apply rule actions to a transaction.

        Args:
            rule: Rule with actions to apply
            transaction: Transaction to modify

        Returns:
            List of applied actions
        """
        actions = rule.actions.get("actions", [])
        applied = []

        for action in actions:
            action_type = action.get("type")
            action_value = action.get("value")

            if not action_type or action_value is None:
                continue

            if action_type == "set_category":
                transaction.category = action_value
                applied.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "action": "set_category",
                        "value": action_value,
                    }
                )

            elif action_type == "add_tag":
                # Initialize tags if None
                if transaction.tags is None:
                    transaction.tags = []

                # Add tag if not already present
                if action_value not in transaction.tags:
                    transaction.tags.append(action_value)
                    applied.append(
                        {
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "action": "add_tag",
                            "value": action_value,
                        }
                    )

            elif action_type == "set_merchant":
                transaction.merchant = action_value
                applied.append(
                    {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "action": "set_merchant",
                        "value": action_value,
                    }
                )

        # Commit changes if any actions were applied
        if applied:
            self.db.commit()

        return applied
