"""SQLAlchemy ORM models for Canopy - Personal Finance Platform."""

from backend.db.models.asset import Asset, AssetType, SyncSource
from backend.db.models.lot import Lot
from backend.db.models.dividend import Dividend, DividendType
from backend.db.models.price_history import PriceHistory
from backend.db.models.portfolio_snapshot import PortfolioSnapshot, SnapshotHolding
from backend.db.models.real_estate import (
    RealEstateProperty,
    RealEstatePaymentSeries,
    RealEstatePayment,
    PaymentStatus,
    PaymentFrequency,
)
from backend.db.models.liability import (
    Liability,
    LiabilityType,
    LiabilityStatus,
    LiabilityBalanceHistory,
    LiabilityPayment,
)

__all__ = [
    # Core assets
    "Asset",
    "AssetType",
    "SyncSource",
    "Lot",
    "Dividend",
    "DividendType",
    "PriceHistory",
    "PortfolioSnapshot",
    "SnapshotHolding",
    # Real estate
    "RealEstateProperty",
    "RealEstatePaymentSeries",
    "RealEstatePayment",
    "PaymentStatus",
    "PaymentFrequency",
    # Liabilities
    "Liability",
    "LiabilityType",
    "LiabilityStatus",
    "LiabilityBalanceHistory",
    "LiabilityPayment",
]
