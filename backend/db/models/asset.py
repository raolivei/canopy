"""Asset model for tracking stocks, ETFs, crypto, retirement accounts, and other investments.

Canopy - Personal Finance Platform
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.lot import Lot
    from backend.db.models.dividend import Dividend
    from backend.db.models.price_history import PriceHistory


class AssetType(str, enum.Enum):
    """Types of assets that can be tracked."""
    # Investment assets
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    BOND = "bond"
    CASH = "cash"
    
    # Bank accounts
    BANK_ACCOUNT = "bank_account"
    BANK_CHECKING = "bank_checking"
    BANK_SAVINGS = "bank_savings"
    
    # Retirement accounts (Canada)
    RETIREMENT_RRSP = "retirement_rrsp"
    RETIREMENT_TFSA = "retirement_tfsa"
    RETIREMENT_FHSA = "retirement_fhsa"
    RETIREMENT_DPSP = "retirement_dpsp"
    
    # Retirement accounts (USA)
    RETIREMENT_401K = "retirement_401k"
    RETIREMENT_IRA = "retirement_ira"
    RETIREMENT_ROTH_IRA = "retirement_roth_ira"
    
    # Alternative investments
    REAL_ESTATE = "real_estate"
    CROWDFUNDING = "crowdfunding"
    PRIVATE_EQUITY = "private_equity"
    
    # Liabilities (tracked with is_liability=True)
    LIABILITY_CREDIT_CARD = "liability_credit_card"
    LIABILITY_LOAN = "liability_loan"
    LIABILITY_MORTGAGE = "liability_mortgage"
    LIABILITY_CAR_LOAN = "liability_car_loan"
    LIABILITY_LINE_OF_CREDIT = "liability_line_of_credit"
    
    OTHER = "other"


class SyncSource(str, enum.Enum):
    """Source of data synchronization for the asset."""
    MANUAL = "manual"
    QUESTRADE = "questrade"
    MOOMOO = "moomoo"
    WISE = "wise"
    WEALTHSIMPLE = "wealthsimple"
    CSV_IMPORT = "csv_import"
    YFINANCE = "yfinance"


class Asset(Base):
    """Represents a financial asset or liability.
    
    Can be: stocks, ETFs, crypto, bank accounts, retirement accounts,
    real estate, credit cards, loans, etc.
    """
    
    __tablename__ = "assets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, values_callable=lambda x: [e.value for e in x]), 
        default=AssetType.STOCK
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD")  # Supports crypto tickers
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Institution and location
    institution: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # RBC, Wealthsimple, Nubank, Clear, XP, etc.
    country: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True
    )  # ISO 3166-1 alpha-2: CA, US, BR
    
    # Liability tracking
    is_liability: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Ownership percentage (for shared assets like the apartment - 0.5 = 50%)
    ownership_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), 
        default=Decimal("1.0")
    )
    
    # Sync source for automatic updates (stored as string to match migration)
    sync_source: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        default="MANUAL"
    )
    
    # External account ID for linking to APIs (Questrade account ID, etc.)
    external_account_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    
    # Current price/balance (cached from last fetch)
    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=8), 
        nullable=True
    )
    price_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # For liabilities: interest rate and credit limit
    interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=4),  # e.g., 0.1999 = 19.99%
        nullable=True
    )
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    
    # Notes for additional context
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Relationships
    lots: Mapped[list["Lot"]] = relationship(
        "Lot", 
        back_populates="asset", 
        cascade="all, delete-orphan"
    )
    dividends: Mapped[list["Dividend"]] = relationship(
        "Dividend", 
        back_populates="asset", 
        cascade="all, delete-orphan"
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", 
        back_populates="asset", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Asset(symbol={self.symbol}, type={self.asset_type}, institution={self.institution})>"
    
    @property
    def is_retirement_account(self) -> bool:
        """Check if this is a retirement account."""
        return self.asset_type.value.startswith("retirement_")
    
    @property
    def is_bank_account(self) -> bool:
        """Check if this is a bank account."""
        return self.asset_type.value.startswith("bank_")
    
    @property
    def effective_value(self) -> Optional[Decimal]:
        """Get the effective value considering ownership percentage.
        
        For shared assets (like the 50/50 apartment), this returns
        the user's portion of the value.
        """
        if self.current_price is None:
            return None
        return self.current_price * self.ownership_percentage
