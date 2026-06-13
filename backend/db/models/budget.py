"""Budget models for tracking spending against limits.

Canopy - Personal Finance Platform
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class PeriodType(str, enum.Enum):
    """Budget period types."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class Budget(Base):
    """A budget for tracking spending against limits."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Budget metadata
    name: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(10), default="CAD")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    categories: Mapped[list["BudgetCategory"]] = relationship(
        "BudgetCategory", back_populates="budget", cascade="all, delete-orphan"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes for common queries
    __table_args__ = (Index("ix_budgets_is_active", "is_active"),)

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, name={self.name}, currency={self.currency})>"


class BudgetCategory(Base):
    """A category within a budget with a spending limit."""

    __tablename__ = "budget_categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"))

    # Category info
    category_name: Mapped[str] = mapped_column(String(100))
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))

    # Period settings
    period_type: Mapped[str] = mapped_column(
        Enum(PeriodType, values_callable=lambda x: [e.value for e in x]), default="monthly"
    )

    # Rollover behavior
    rollover_excess: Mapped[bool] = mapped_column(default=False)

    # Relationship
    budget: Mapped["Budget"] = relationship("Budget", back_populates="categories")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_budget_categories_budget_id", "budget_id"),
        Index("ix_budget_categories_category_name", "category_name"),
    )

    def __repr__(self) -> str:
        return f"<BudgetCategory(id={self.id}, budget_id={self.budget_id}, category={self.category_name})>"


class BudgetTracking(Base):
    """Tracks actual spending against budget categories for a given period."""

    __tablename__ = "budget_tracking"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Reference
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"))
    budget_category_id: Mapped[int] = mapped_column(
        ForeignKey("budget_categories.id", ondelete="CASCADE")
    )

    # Period tracking
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Actual spending
    actual_spent: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), default=0)
    actual_spent_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Rollover from previous period (if enabled)
    rollover_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_budget_tracking_budget_id", "budget_id"),
        Index("ix_budget_tracking_period", "period_start", "period_end"),
        Index("ix_budget_tracking_category", "budget_category_id"),
    )

    def __repr__(self) -> str:
        return f"<BudgetTracking(id={self.id}, budget_id={self.budget_id}, period={self.period_start})>"
