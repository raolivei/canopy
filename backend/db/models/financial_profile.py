"""Financial profile model for the Neural Economic Growth Advisor.

Canopy - Personal Finance Platform

Stores the user's financial situation, goals, and preferences
for tax-aware cross-border wealth projections.
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class VisaType(str, enum.Enum):
    """Visa/immigration status."""
    CITIZEN = "citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    WORK_PERMIT = "work_permit"
    TN = "tn"           # TN visa (CA/MX professionals in US)
    H1B = "h1b"
    L1 = "l1"
    O1 = "o1"
    STUDENT = "student"
    OTHER = "other"


class EmploymentType(str, enum.Enum):
    """Employment classification for tax purposes."""
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    SELF_EMPLOYED = "self_employed"


class AdvisorGoal(str, enum.Enum):
    """Financial and life goals for planning."""
    FIRE = "fire"                         # Financial independence / retire early
    GREEN_CARD = "green_card"             # Obtain US permanent residency
    RELOCATION_US = "relocation_us"       # Move to the US
    RELOCATION_CA = "relocation_ca"       # Move to Canada
    RELOCATION_BR = "relocation_br"       # Move to Brazil
    HOME_PURCHASE = "home_purchase"       # Buy a home
    FHSA_ELIGIBLE = "fhsa_eligible"       # First Home Savings Account eligible
    MINIMIZE_TAX = "minimize_tax"         # Optimize for lowest tax burden
    MAXIMIZE_GROWTH = "maximize_growth"   # Optimize for highest net worth


class FinancialProfile(Base):
    """User's financial profile for the Growth Advisor.

    Single-user app — at most one row. Stores all inputs needed
    for tax-aware multi-year projections.
    """

    __tablename__ = "financial_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Location & Immigration ---
    country_of_residence: Mapped[str] = mapped_column(
        String(2), nullable=False, default="CA"
    )  # ISO 3166-1 alpha-2: CA, US, BR
    province_or_state: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # e.g. ON, BC, NY, CA (US state)
    citizenship: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True
    )  # Country of citizenship ISO code
    visa_type: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default=VisaType.CITIZEN.value
    )

    # --- Income ---
    annual_gross_income: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False, default=Decimal("0")
    )
    income_currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="CAD"
    )
    employment_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=EmploymentType.EMPLOYEE.value
    )

    # --- Cash Flow ---
    monthly_expenses: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False, default=Decimal("0")
    )
    monthly_savings: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False, default=Decimal("0")
    )

    # --- Goals (stored as JSON array of AdvisorGoal values) ---
    goals: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list
    )

    # --- Planning Horizon ---
    target_retirement_age: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    current_age: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    projection_years: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )

    # --- Notes ---
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialProfile(country={self.country_of_residence}, "
            f"income={self.annual_gross_income} {self.income_currency})>"
        )
