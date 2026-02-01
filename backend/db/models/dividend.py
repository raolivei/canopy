"""Dividend model for tracking dividend payments."""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.asset import Asset


class DividendType(str, enum.Enum):
    """Types of dividend payments."""
    CASH = "cash"
    STOCK = "stock"
    REINVESTED = "reinvested"  # DRIP


class Dividend(Base):
    """Represents a dividend payment received."""
    
    __tablename__ = "dividends"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    
    # Dividend details
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4))
    payment_date: Mapped[date] = mapped_column(Date, index=True)
    dividend_type: Mapped[DividendType] = mapped_column(
        Enum(DividendType), 
        default=DividendType.CASH
    )
    
    # For stock dividends or reinvested dividends
    shares_received: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8), 
        nullable=True
    )
    
    # Optional metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="dividends")
    
    def __repr__(self) -> str:
        return f"<Dividend(asset_id={self.asset_id}, amount={self.amount}, date={self.payment_date})>"
