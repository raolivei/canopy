"""Real Estate model for tracking property investments with payment schedules.

Canopy - Personal Finance Platform

Supports:
- Property ownership with partnership splits (e.g., 50/50 with Alex)
- Payment schedules with multiple series (ATO, SINAL, MENSAIS, SEMESTRAIS, etc.)
- Payment tracking (paid, ongoing, not started)
- Property value estimation
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class PaymentStatus(str, enum.Enum):
    """Status of a payment in the schedule."""
    PAID = "paid"
    ONGOING = "ongoing"
    NOT_STARTED = "not_started"
    OVERDUE = "overdue"


class PaymentFrequency(str, enum.Enum):
    """Frequency of payments."""
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class RealEstateProperty(Base):
    """Represents a real estate property investment."""
    
    __tablename__ = "real_estate_properties"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Property identification
    name: Mapped[str] = mapped_column(String(255))  # e.g., "Apartamento Porto Alegre"
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="BR")  # ISO 3166-1 alpha-2
    
    # Financial details
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    total_contract_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2)
    )  # Total value of the property in contract
    
    # Ownership
    ownership_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4),
        default=Decimal("1.0")
    )  # 0.5 = 50% ownership
    
    # Partners (for shared ownership)
    partner_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    partner_ownership_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=4),
        nullable=True
    )
    
    # Value estimation
    estimated_market_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    value_estimated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Purchase details
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rented: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_rent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    payment_series: Mapped[list["RealEstatePaymentSeries"]] = relationship(
        "RealEstatePaymentSeries",
        back_populates="property",
        cascade="all, delete-orphan"
    )
    payments: Mapped[list["RealEstatePayment"]] = relationship(
        "RealEstatePayment",
        back_populates="real_estate_property",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<RealEstateProperty(name={self.name}, ownership={self.ownership_percentage})>"
    
    @property
    def total_paid(self) -> Decimal:
        """Calculate total amount paid so far (user's share)."""
        return sum(
            (p.amount_paid or Decimal("0")) * self.ownership_percentage
            for p in self.payments
            if p.status == PaymentStatus.PAID
        )
    
    @property
    def total_remaining(self) -> Decimal:
        """Calculate total amount remaining to pay (user's share)."""
        total = self.total_contract_value * self.ownership_percentage
        return total - self.total_paid
    
    @property
    def equity_percentage(self) -> Decimal:
        """Calculate how much of the property has been paid off."""
        if self.total_contract_value == 0:
            return Decimal("0")
        return (self.total_paid / (self.total_contract_value * self.ownership_percentage)) * 100
    
    @property
    def user_market_value(self) -> Optional[Decimal]:
        """Get the user's share of the estimated market value."""
        if self.estimated_market_value is None:
            return None
        return self.estimated_market_value * self.ownership_percentage


class RealEstatePaymentSeries(Base):
    """Represents a series of payments for a property.
    
    Examples: ATO, SINAL, MENSAIS 2024, MENSAIS 2025, SEMESTRAIS, UNICA
    """
    
    __tablename__ = "real_estate_payment_series"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("real_estate_properties.id", ondelete="CASCADE")
    )
    
    # Series identification
    name: Mapped[str] = mapped_column(String(100))  # e.g., "MENSAIS 2025"
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Payment details
    frequency: Mapped[PaymentFrequency] = mapped_column(
        Enum(PaymentFrequency),
        default=PaymentFrequency.MONTHLY
    )
    total_installments: Mapped[int] = mapped_column(default=1)
    nominal_amount_per_installment: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2)
    )
    
    # Schedule
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.NOT_STARTED
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    property: Mapped["RealEstateProperty"] = relationship(
        "RealEstateProperty",
        back_populates="payment_series"
    )
    
    def __repr__(self) -> str:
        return f"<RealEstatePaymentSeries(name={self.name}, installments={self.total_installments})>"


class RealEstatePayment(Base):
    """Represents an individual payment for a property."""
    
    __tablename__ = "real_estate_payments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("real_estate_properties.id", ondelete="CASCADE")
    )
    series_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("real_estate_payment_series.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Payment details
    description: Mapped[str] = mapped_column(String(255))
    due_date: Mapped[date] = mapped_column(Date)
    
    # Amounts
    nominal_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2)
    )  # Original amount without corrections
    amount_with_correction: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )  # Amount with inflation/interest corrections
    amount_paid: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )  # Actual amount paid
    
    # Payment info
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.NOT_STARTED
    )
    
    # Split tracking (for 50/50 ownership)
    is_split: Mapped[bool] = mapped_column(Boolean, default=True)
    paid_by_user: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    real_estate_property: Mapped["RealEstateProperty"] = relationship(
        "RealEstateProperty",
        back_populates="payments"
    )
    
    def __repr__(self) -> str:
        return f"<RealEstatePayment(description={self.description}, status={self.status})>"
    
    @property
    def effective_amount(self) -> Decimal:
        """Get the effective amount (with correction if available, otherwise nominal)."""
        return self.amount_with_correction or self.nominal_amount
