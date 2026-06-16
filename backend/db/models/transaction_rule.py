"""Transaction rules for automatic categorization and tagging.

Canopy - Personal Finance Platform
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class TransactionRule(Base):
    """Rule for automatic transaction categorization and tagging.

    Rules are evaluated in priority order (highest first) against
    incoming transactions. Each rule consists of conditions that must
    be met and actions to apply when matched.

    Example rule structure:
        {
            "conditions": [
                {"field": "merchant", "operator": "contains", "value": "Starbucks"}
            ],
            "actions": [
                {"type": "set_category", "value": "Dining"},
                {"type": "add_tag", "value": "coffee"}
            ]
        }

    Supported operators:
        - String: contains, equals, starts_with, ends_with, regex
        - Numeric: gt, lt, gte, lte
        - Array: in, not_in

    Supported actions:
        - set_category: Set transaction category
        - add_tag: Add tag to transaction
        - set_merchant: Override merchant name
    """

    __tablename__ = "transaction_rules"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Rule identification
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Execution priority (higher = evaluated first)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Rule definition (JSONB for flexibility)
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Control flags
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    stop_on_match: Mapped[bool] = mapped_column(Boolean, default=False)  # Stop evaluating other rules if matched

    # Usage statistics
    match_count: Mapped[int] = mapped_column(Integer, default=0)
    last_matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes for efficient query and sorting
    __table_args__ = (
        Index("ix_transaction_rules_active", "active"),
        Index("ix_transaction_rules_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"<TransactionRule(id={self.id}, name={self.name}, priority={self.priority}, active={self.active})>"
