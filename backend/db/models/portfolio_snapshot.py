"""Portfolio snapshot models for historical portfolio value tracking."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.asset import Asset


class PortfolioSnapshot(Base):
    """Daily snapshot of total portfolio value."""
    
    __tablename__ = "portfolio_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    
    # Aggregate values
    total_value: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4))
    total_cost_basis: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    holdings: Mapped[list["SnapshotHolding"]] = relationship(
        "SnapshotHolding",
        back_populates="snapshot",
        cascade="all, delete-orphan"
    )
    
    @property
    def total_gain_loss(self) -> Decimal:
        """Total unrealized gain/loss."""
        return self.total_value - self.total_cost_basis
    
    @property
    def total_return_pct(self) -> Optional[Decimal]:
        """Total return percentage."""
        if self.total_cost_basis == 0:
            return None
        return (self.total_gain_loss / self.total_cost_basis) * 100
    
    def __repr__(self) -> str:
        return f"<PortfolioSnapshot(date={self.snapshot_date}, value={self.total_value})>"


class SnapshotHolding(Base):
    """Individual holding within a portfolio snapshot."""
    
    __tablename__ = "snapshot_holdings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_snapshots.id"), 
        index=True
    )
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    
    # Position data at snapshot time
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    market_value: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4))
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4))
    price_at_snapshot: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    
    # Relationships
    snapshot: Mapped["PortfolioSnapshot"] = relationship(
        "PortfolioSnapshot", 
        back_populates="holdings"
    )
    asset: Mapped["Asset"] = relationship("Asset")
    
    # Composite index
    __table_args__ = (
        Index("ix_snapshot_holdings_snapshot_asset", "snapshot_id", "asset_id"),
    )
    
    @property
    def gain_loss(self) -> Decimal:
        """Unrealized gain/loss for this holding."""
        return self.market_value - self.cost_basis
    
    @property
    def return_pct(self) -> Optional[Decimal]:
        """Return percentage for this holding."""
        if self.cost_basis == 0:
            return None
        return (self.gain_loss / self.cost_basis) * 100
    
    def __repr__(self) -> str:
        return f"<SnapshotHolding(snapshot_id={self.snapshot_id}, asset_id={self.asset_id})>"
