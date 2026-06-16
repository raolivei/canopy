"""Budget models for tracking spending budgets and limits.

Canopy - Personal Finance Platform
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    pass


class BudgetPeriodType(str, enum.Enum):
    """Period type for budget recurrence."""

    MONTHLY = "monthly"
    YEARLY = "yearly"


class Budget(Base):
    """A budget for tracking spending limits.

    Can be monthly or yearly, with optional category breakdowns.
    """

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))
    period: Mapped[BudgetPeriodType] = mapped_column(
        Enum(BudgetPeriodType, values_callable=lambda x: [e.value for e in x]), default=BudgetPeriodType.MONTHLY
    )

    # Optional user_id for future multi-user support (nullable for single-user)
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Active status for soft deletion
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    categories: Mapped[list["BudgetCategory"]] = relationship(
        "BudgetCategory", back_populates="budget", cascade="all, delete-orphan"
    )
    periods: Mapped[list["BudgetPeriod"]] = relationship(
        "BudgetPeriod", back_populates="budget", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_budgets_user_id", "user_id"),
        Index("ix_budgets_active", "active"),
    )

    def __repr__(self) -> str:
        return f"<Budget(id={self.id}, name={self.name}, amount={self.amount}, period={self.period})>"


class BudgetCategory(Base):
    """Category-specific spending limit within a budget.

    Allows breaking down a budget into category-level limits
    (e.g., $500 for groceries, $200 for dining).
    """

    __tablename__ = "budget_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category_name: Mapped[str] = mapped_column(String(100))
    amount_limit: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="categories")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("budget_id", "category_name", name="uq_budget_category"),
        Index("ix_budget_categories_budget_id", "budget_id"),
    )

    def __repr__(self) -> str:
        return f"<BudgetCategory(id={self.id}, budget_id={self.budget_id}, category={self.category_name}, limit={self.amount_limit})>"


class BudgetPeriod(Base):
    """Tracks actual spending for a specific budget period.

    Each period represents one recurrence of the budget
    (e.g., January 2026 for a monthly budget).
    """

    __tablename__ = "budget_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    actual_spent: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2), default=Decimal("0.00"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    budget: Mapped["Budget"] = relationship("Budget", back_populates="periods")

    # Indexes for date range queries
    __table_args__ = (
        Index("ix_budget_periods_budget_id", "budget_id"),
        Index("ix_budget_periods_dates", "period_start", "period_end"),
    )

    def __repr__(self) -> str:
        return f"<BudgetPeriod(id={self.id}, budget_id={self.budget_id}, start={self.period_start}, end={self.period_end}, spent={self.actual_spent})>"
