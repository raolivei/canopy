"""Recurring transaction pattern model for tracking user-approved patterns.

Canopy - Personal Finance Platform
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class RecurringFrequency(str, enum.Enum):
    """Recurring transaction frequency."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class RecurringPattern(Base):
    """A user-approved recurring transaction pattern."""

    __tablename__ = "recurring_patterns"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Pattern identification
    merchant: Mapped[str] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Amount information
    average_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))
    amount_variance: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))  # ±tolerance

    # Frequency and prediction
    frequency: Mapped[str] = mapped_column(String(20), default=RecurringFrequency.MONTHLY.value)
    next_expected: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Confidence scoring
    confidence: Mapped[int] = mapped_column(default=0)  # 0-100

    # Historical occurrences (for reference/visualization)
    occurrences: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Known skips or delays
    should_skip_dates: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_recurring_patterns_merchant", "merchant"),
        Index("ix_recurring_patterns_is_active", "is_active"),
        Index("ix_recurring_patterns_next_expected", "next_expected"),
    )

    def __repr__(self) -> str:
        return f"<RecurringPattern(id={self.id}, merchant={self.merchant}, frequency={self.frequency})>"
