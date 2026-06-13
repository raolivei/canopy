"""Category model for transaction categorization with hierarchy support.

Canopy - Personal Finance Platform
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.transaction import Transaction


class Category(Base):
    """A transaction category with optional hierarchy (parent-child relationships).

    Categories can be organized hierarchically (e.g., Expenses > Groceries)
    and can optionally preserve Monarch Money's original category names
    for import tracking.
    """

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Category naming and display
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Hierarchy support
    parent_category_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Monarch Money integration
    monarch_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Original category name from Monarch

    # UI metadata
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color (#RRGGBB)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Icon name (e.g., "shopping-cart")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="children", foreign_keys=[parent_category_id]
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="category_obj", foreign_keys="Transaction.category_id"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_categories_name", "name"),
        Index("ix_categories_monarch_name", "monarch_name"),
        Index("ix_categories_parent_id", "parent_category_id"),
        Index("ix_categories_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        parent_name = f" (parent={self.parent.name})" if self.parent else ""
        return f"<Category(id={self.id}, name={self.name}{parent_name})>"

    def get_path(self) -> list["Category"]:
        """Get the full path from root to this category (inclusive).

        Returns:
            List of categories from root ancestor to this category.
        """
        path = [self]
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path

    def get_path_str(self, separator: str = " > ") -> str:
        """Get the full path as a formatted string.

        Args:
            separator: String to join path segments (default: " > ")

        Returns:
            Formatted path string, e.g., "Expenses > Groceries"
        """
        return separator.join(c.name for c in self.get_path())

    def get_children(self) -> list["Category"]:
        """Get immediate child categories.

        Returns:
            List of direct children.
        """
        return self.children

    def get_descendants(self) -> list["Category"]:
        """Get all descendant categories (recursive).

        Returns:
            List of all descendants at any depth.
        """
        descendants = list(self.children)
        for child in self.children:
            descendants.extend(child.get_descendants())
        return descendants

    def is_root(self) -> bool:
        """Check if this is a root category (no parent)."""
        return self.parent is None

    def is_leaf(self) -> bool:
        """Check if this is a leaf category (no children)."""
        return len(self.children) == 0
