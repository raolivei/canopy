"""Transaction model for tracking income, expenses, and transfers.

Canopy - Personal Finance Platform
"""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Index, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class TransactionType(str, enum.Enum):
    """Types of financial transactions."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    BUY = "buy"  # Investment purchase
    SELL = "sell"  # Investment sale


class Transaction(Base):
    """A financial transaction (income, expense, or transfer)."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Core transaction data
    description: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))
    currency: Mapped[str] = mapped_column(String(10), default="CAD")
    type: Mapped[str] = mapped_column(String(20), default="expense")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Categorization
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Merchant info (from Monarch/bank data)
    merchant: Mapped[str | None] = mapped_column(String(200), nullable=True)
    original_statement: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Additional metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # PostgreSQL stores a native text[]; SQLite (tests) falls back to JSON so
    # Python lists bind and round-trip without a custom type adapter.
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String).with_variant(JSON(), "sqlite"), nullable=True)

    # Investment transaction fields
    ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shares: Mapped[Decimal | None] = mapped_column(Numeric(precision=18, scale=8), nullable=True)
    price_per_share: Mapped[Decimal | None] = mapped_column(Numeric(precision=18, scale=8), nullable=True)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(precision=18, scale=2), nullable=True)

    # Import tracking
    import_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    import_source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "monarch", "rbc"

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_transactions_date", "date"),
        Index("ix_transactions_category", "category"),
        Index("ix_transactions_type", "type"),
        Index("ix_transactions_account", "account"),
        Index("ix_transactions_merchant", "merchant"),
        # Composite indexes created by migration 20260615_0014 (date descending)
        Index("idx_transactions_date_type", text("date DESC"), "type"),
        Index("idx_transactions_category_date", "category", text("date DESC")),
        Index("idx_transactions_date_type_category", text("date DESC"), "type", "category"),
        Index(
            "idx_transactions_merchant_date",
            "merchant",
            text("date DESC"),
            postgresql_where=text("merchant IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, type={self.type})>"
