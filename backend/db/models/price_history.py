"""Price history model for tracking historical asset prices."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.asset import Asset


class PriceHistory(Base):
    """Stores historical price data for assets."""
    
    __tablename__ = "price_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    
    # Price data
    price: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="price_history")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_price_history_asset_fetched", "asset_id", "fetched_at"),
    )
    
    def __repr__(self) -> str:
        return f"<PriceHistory(asset_id={self.asset_id}, price={self.price}, at={self.fetched_at})>"
