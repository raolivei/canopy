"""Transaction rules engine for auto-categorization, tagging, and splitting.

Canopy - Personal Finance Platform
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from backend.db.base import Base


class RuleConditionField(str, enum.Enum):
    """Transaction fields that can be used in rule conditions."""

    MERCHANT = "merchant"
    AMOUNT = "amount"
    DESCRIPTION = "description"
    CATEGORY = "category"
    ACCOUNT = "account"
    ORIGINAL_STATEMENT = "original_statement"
    TAGS = "tags"


class RuleConditionOperator(str, enum.Enum):
    """Operators for evaluating rule conditions."""

    EQUALS = "equals"
    CONTAINS = "contains"
    REGEX = "regex"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"


class RuleActionType(str, enum.Enum):
    """Types of actions that rules can perform."""

    SET_CATEGORY = "set_category"
    ADD_TAG = "add_tag"
    SPLIT = "split"


class Rule(Base):
    """A rule for automatically processing transactions."""

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Rule metadata
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = applied first

    # Relationships
    conditions: Mapped[list["RuleCondition"]] = relationship(
        "RuleCondition",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    actions: Mapped[list["RuleAction"]] = relationship(
        "RuleAction",
        back_populates="rule",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_rules_active_priority", "is_active", "priority"),
        Index("ix_rules_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Rule(id={self.id}, name={self.name}, priority={self.priority})>"


class RuleCondition(Base):
    """A condition that must be matched for a rule to apply."""

    __tablename__ = "rule_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("rules.id", ondelete="CASCADE"))

    # Condition definition
    field: Mapped[str] = mapped_column(Enum(RuleConditionField), nullable=False)
    operator: Mapped[str] = mapped_column(Enum(RuleConditionOperator), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)

    # For numeric comparisons
    numeric_value: Mapped[Optional[Decimal]] = mapped_column(
        nullable=True, precision=18, scale=2
    )

    # Relationship
    rule: Mapped["Rule"] = relationship("Rule", back_populates="conditions")

    __table_args__ = (Index("ix_rule_conditions_rule_id", "rule_id"),)

    def __repr__(self) -> str:
        return f"<RuleCondition(id={self.id}, field={self.field}, operator={self.operator})>"


class RuleAction(Base):
    """An action to perform when a rule matches."""

    __tablename__ = "rule_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("rules.id", ondelete="CASCADE"))

    # Action definition
    action_type: Mapped[str] = mapped_column(Enum(RuleActionType), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)  # Execution order within rule

    # Action value varies by type:
    # SET_CATEGORY: target category name
    # ADD_TAG: tag name
    # SPLIT: JSON with splits [{category: str, percentage: float}, ...]
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # For split actions, store structured data
    split_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationship
    rule: Mapped["Rule"] = relationship("Rule", back_populates="actions")

    __table_args__ = (Index("ix_rule_actions_rule_id", "rule_id"),)

    def __repr__(self) -> str:
        return f"<RuleAction(id={self.id}, type={self.action_type}, order={self.order})>"
