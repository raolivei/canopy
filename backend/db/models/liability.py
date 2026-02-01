"""Liability model for tracking credit cards, loans, and other debts.

Canopy - Personal Finance Platform

Supports:
- Credit cards with credit limits and APR
- Loans (car, personal, student, etc.) with amortization
- Lines of credit
- Payment tracking and history
- Minimum payment calculations
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


class LiabilityType(str, enum.Enum):
    """Types of liabilities."""
    CREDIT_CARD = "credit_card"
    CAR_LOAN = "car_loan"
    PERSONAL_LOAN = "personal_loan"
    STUDENT_LOAN = "student_loan"
    MORTGAGE = "mortgage"
    LINE_OF_CREDIT = "line_of_credit"
    OTHER = "other"


class LiabilityStatus(str, enum.Enum):
    """Status of a liability."""
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class Liability(Base):
    """Represents a liability (debt) such as credit cards, loans, etc."""
    
    __tablename__ = "liabilities"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Identification
    name: Mapped[str] = mapped_column(String(255))  # e.g., "RBC VISA 7192"
    institution: Mapped[str] = mapped_column(String(100))  # e.g., "RBC", "Scotiabank"
    account_number_last4: Mapped[Optional[str]] = mapped_column(
        String(4), nullable=True
    )  # Last 4 digits for identification
    
    # Type and status
    liability_type: Mapped[LiabilityType] = mapped_column(
        Enum(LiabilityType),
        default=LiabilityType.CREDIT_CARD
    )
    status: Mapped[LiabilityStatus] = mapped_column(
        Enum(LiabilityStatus),
        default=LiabilityStatus.ACTIVE
    )
    
    # Currency and country
    currency: Mapped[str] = mapped_column(String(3), default="CAD")
    country: Mapped[str] = mapped_column(String(2), default="CA")
    
    # Balance tracking
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        default=Decimal("0")
    )
    balance_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Credit details (for credit cards and lines of credit)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    available_credit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    
    # Interest rates
    apr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=4),  # e.g., 0.1999 = 19.99%
        nullable=True
    )
    promotional_apr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=4),
        nullable=True
    )
    promotional_apr_end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    
    # Loan-specific fields
    original_principal: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )  # Original loan amount
    loan_term_months: Mapped[Optional[int]] = mapped_column(nullable=True)
    loan_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    loan_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Payment details
    minimum_payment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    fixed_payment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )  # For loans with fixed monthly payments
    payment_due_day: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )  # Day of month (1-31)
    next_payment_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Statement details
    statement_closing_day: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )  # Day of month statement closes
    last_statement_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    last_statement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Rewards (for credit cards)
    rewards_program: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g., "WestJet Dollars", "Aeroplan"
    annual_fee: Mapped[Optional[Decimal]] = mapped_column(
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
    balance_history: Mapped[list["LiabilityBalanceHistory"]] = relationship(
        "LiabilityBalanceHistory",
        back_populates="liability",
        cascade="all, delete-orphan"
    )
    payments: Mapped[list["LiabilityPayment"]] = relationship(
        "LiabilityPayment",
        back_populates="liability",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Liability(name={self.name}, balance={self.current_balance}, type={self.liability_type})>"
    
    @property
    def utilization_percentage(self) -> Optional[Decimal]:
        """Calculate credit utilization for credit cards/lines of credit."""
        if self.credit_limit is None or self.credit_limit == 0:
            return None
        return (self.current_balance / self.credit_limit) * 100
    
    @property
    def months_remaining(self) -> Optional[int]:
        """Calculate months remaining on a loan."""
        if self.loan_end_date is None:
            return None
        today = date.today()
        if self.loan_end_date <= today:
            return 0
        return (self.loan_end_date.year - today.year) * 12 + (self.loan_end_date.month - today.month)
    
    @property
    def is_high_utilization(self) -> bool:
        """Check if credit utilization is above 30% (affects credit score)."""
        util = self.utilization_percentage
        if util is None:
            return False
        return util > 30


class LiabilityBalanceHistory(Base):
    """Historical balance tracking for liabilities."""
    
    __tablename__ = "liability_balance_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    liability_id: Mapped[int] = mapped_column(
        ForeignKey("liabilities.id", ondelete="CASCADE")
    )
    
    # Balance snapshot
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Optional: statement info
    is_statement_balance: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    liability: Mapped["Liability"] = relationship(
        "Liability",
        back_populates="balance_history"
    )
    
    def __repr__(self) -> str:
        return f"<LiabilityBalanceHistory(balance={self.balance}, date={self.recorded_at})>"


class LiabilityPayment(Base):
    """Payment records for liabilities."""
    
    __tablename__ = "liability_payments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    liability_id: Mapped[int] = mapped_column(
        ForeignKey("liabilities.id", ondelete="CASCADE")
    )
    
    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=2))
    payment_date: Mapped[date] = mapped_column(Date)
    
    # Breakdown (for loans)
    principal_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    interest_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=True
    )
    
    # Payment method
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "auto-pay", "manual", "bank transfer"
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    liability: Mapped["Liability"] = relationship(
        "Liability",
        back_populates="payments"
    )
    
    def __repr__(self) -> str:
        return f"<LiabilityPayment(amount={self.amount}, date={self.payment_date})>"
