"""Lot model for cost basis tracking of individual purchases."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.asset import Asset


class Lot(Base):
    """Represents a single purchase lot for cost basis tracking.
    
    Each buy transaction creates a new lot. When selling, lots can be
    marked as sold (FIFO, LIFO, or specific lot selection).
    """
    
    __tablename__ = "lots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    
    # Purchase details
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    fees: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), default=Decimal("0"))
    purchase_date: Mapped[date] = mapped_column(Date)
    
    # Optional metadata
    account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Sale tracking
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    sold_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sold_price_per_unit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8), 
        nullable=True
    )
    sold_fees: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=4), 
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="lots")
    
    @property
    def cost_basis(self) -> Decimal:
        """Total cost basis including fees."""
        return (self.quantity * self.price_per_unit) + self.fees
    
    @property
    def realized_gain_loss(self) -> Optional[Decimal]:
        """Realized gain/loss if lot is sold."""
        if not self.is_sold or self.sold_price_per_unit is None:
            return None
        proceeds = (self.quantity * self.sold_price_per_unit) - (self.sold_fees or Decimal("0"))
        return proceeds - self.cost_basis
    
    def __repr__(self) -> str:
        return f"<Lot(asset_id={self.asset_id}, qty={self.quantity}, date={self.purchase_date})>"
