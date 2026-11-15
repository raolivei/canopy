"""Pydantic schemas for Portfolio API requests and responses."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from backend.db.models.asset import AssetType
from backend.db.models.dividend import DividendType

# ============== Asset Schemas ==============


class AssetCreate(BaseModel):
    """Schema for creating a new asset."""

    symbol: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    asset_type: AssetType = Field(default=AssetType.STOCK, description="Type of asset")
    currency: str = Field(default="USD", min_length=3, max_length=3)


class AssetResponse(BaseModel):
    """Schema for asset response."""

    id: int
    symbol: str
    name: str
    asset_type: AssetType
    currency: str
    created_at: datetime
    current_price: Decimal | None = None
    price_updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssetWithHoldings(AssetResponse):
    """Asset with calculated holdings data."""

    total_shares: Decimal = Field(default=Decimal("0"))
    average_cost: Decimal | None = None
    total_cost_basis: Decimal = Field(default=Decimal("0"))
    market_value: Decimal | None = None
    unrealized_gain_loss: Decimal | None = None
    return_pct: Decimal | None = None


# ============== Lot Schemas ==============


class LotCreate(BaseModel):
    """Schema for creating a new lot (purchase)."""

    asset_id: int = Field(..., description="ID of the asset being purchased")
    quantity: Decimal = Field(..., gt=0, description="Number of shares/units")
    price_per_unit: Decimal = Field(..., gt=0, description="Price per share/unit")
    fees: Decimal = Field(default=Decimal("0"), ge=0, description="Transaction fees")
    purchase_date: date = Field(..., description="Date of purchase")
    account: str | None = Field(None, max_length=100, description="Brokerage account")
    notes: str | None = Field(None, description="Optional notes")


class LotSell(BaseModel):
    """Schema for selling a lot."""

    sold_date: date = Field(..., description="Date of sale")
    sold_price_per_unit: Decimal = Field(..., gt=0, description="Sale price per share")
    sold_fees: Decimal = Field(default=Decimal("0"), ge=0, description="Sale transaction fees")


class LotResponse(BaseModel):
    """Schema for lot response."""

    id: int
    asset_id: int
    quantity: Decimal
    price_per_unit: Decimal
    fees: Decimal
    purchase_date: date
    account: str | None = None
    notes: str | None = None
    is_sold: bool
    sold_date: date | None = None
    sold_price_per_unit: Decimal | None = None
    sold_fees: Decimal | None = None
    created_at: datetime

    # Calculated fields
    cost_basis: Decimal
    realized_gain_loss: Decimal | None = None

    model_config = {"from_attributes": True}


# ============== Dividend Schemas ==============


class DividendCreate(BaseModel):
    """Schema for recording a dividend."""

    asset_id: int = Field(..., description="ID of the asset")
    amount: Decimal = Field(..., gt=0, description="Dividend amount")
    payment_date: date = Field(..., description="Date dividend was paid")
    dividend_type: DividendType = Field(default=DividendType.CASH)
    shares_received: Decimal | None = Field(None, ge=0, description="For stock/reinvested dividends")
    notes: str | None = None


class DividendResponse(BaseModel):
    """Schema for dividend response."""

    id: int
    asset_id: int
    amount: Decimal
    payment_date: date
    dividend_type: DividendType
    shares_received: Decimal | None = None
    notes: str | None = None
    created_at: datetime

    # Include asset info
    asset_symbol: str | None = None

    model_config = {"from_attributes": True}


# ============== Portfolio Summary Schemas ==============


class HoldingSummary(BaseModel):
    """Summary of a single holding."""

    asset_id: int
    symbol: str
    name: str
    asset_type: AssetType
    currency: str = "CAD"
    total_shares: Decimal
    average_cost: Decimal
    current_price: Decimal | None = None
    cost_basis: Decimal
    market_value: Decimal | None = None
    unrealized_gain_loss: Decimal | None = None
    return_pct: Decimal | None = None
    allocation_pct: Decimal | None = None


class PortfolioSummary(BaseModel):
    """Complete portfolio summary with metrics."""

    total_value: Decimal | None = None
    total_cost_basis: Decimal
    total_gain_loss: Decimal | None = None
    total_return_pct: Decimal | None = None
    total_dividends: Decimal
    holdings_count: int
    holdings: list[HoldingSummary]


class AllocationItem(BaseModel):
    """Single allocation item for pie chart."""

    asset_type: AssetType
    value: Decimal
    percentage: Decimal
    count: int


class PortfolioAllocation(BaseModel):
    """Portfolio allocation breakdown."""

    by_asset_type: list[AllocationItem]
    total_value: Decimal


# ============== Performance Schemas ==============


class PerformancePoint(BaseModel):
    """Single point in performance history."""

    date: date
    total_value: Decimal
    total_cost_basis: Decimal
    gain_loss: Decimal
    return_pct: Decimal | None = None


class PortfolioPerformance(BaseModel):
    """Historical portfolio performance."""

    period: str  # 7d, 30d, 90d, 1y, all
    data_points: list[PerformancePoint]
    start_value: Decimal | None = None
    end_value: Decimal | None = None
    period_return: Decimal | None = None
    period_return_pct: Decimal | None = None
