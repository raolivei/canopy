"""Category model for transaction categorization taxonomy.

Canopy - Personal Finance Platform
"""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class CategoryIcon(str, enum.Enum):
    """Standard icons for categories."""

    # Income
    SALARY = "💰"
    INVESTMENT = "📈"
    BUSINESS = "💼"

    # Food & Dining
    GROCERIES = "🛒"
    DINING = "🍽️"
    COFFEE = "☕"

    # Transportation
    GAS = "⛽"
    PARKING = "🅿️"
    PUBLIC_TRANSIT = "🚌"
    AUTO = "🚗"

    # Bills & Utilities
    UTILITIES = "💡"
    PHONE = "📱"
    INTERNET = "🌐"

    # Shopping
    SHOPPING = "🛍️"
    CLOTHING = "👔"
    ELECTRONICS = "💻"

    # Entertainment
    ENTERTAINMENT = "🎭"
    MOVIES = "🎬"
    MUSIC = "🎵"
    SPORTS = "⚽"

    # Healthcare
    HEALTHCARE = "🏥"
    PHARMACY = "💊"

    # Housing
    RENT = "🏠"
    MORTGAGE = "🏘️"
    HOME_IMPROVEMENT = "🔧"

    # Education
    EDUCATION = "📚"

    # Travel
    TRAVEL = "✈️"
    HOTEL = "🏨"

    # Personal Care
    PERSONAL_CARE = "💇"

    # Pets
    PETS = "🐾"

    # Gifts & Donations
    GIFTS = "🎁"
    CHARITY = "❤️"

    # Fees & Charges
    FEES = "💸"
    TAXES = "🏛️"

    # Other
    OTHER = "📌"
    UNCATEGORIZED = "❓"


class Category(Base):
    """Transaction category with hierarchical taxonomy support."""

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Category details
    name: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Visual representation
    icon: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Hex color or Tailwind class

    # Hierarchical structure (2-level: parent → child)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )

    # System categories (cannot be deleted/modified by users)
    is_system: Mapped[bool] = mapped_column(default=True)

    # Active status
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_categories_name", "name"),
        Index("ix_categories_parent_id", "parent_id"),
        Index("ix_categories_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, parent_id={self.parent_id})>"
