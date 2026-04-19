"""Portfolio review snapshots (CAD only, Canadian holdings).

Manual / CSV import of dated snapshots for holdings that don't auto-sync via
Wealthsimple. One row per spreadsheet line (same ticker on two brokers = two
lines). Values are always CAD; the app no longer tracks multi-currency or
multi-region portfolios.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    pass


class ReviewSource(str, Enum):
    """How the review was created."""

    MANUAL = "manual"
    CSV_IMPORT = "csv_import"


class PortfolioReview(Base):
    """One Canadian portfolio review as-of a date."""

    __tablename__ = "portfolio_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReviewSource.CSV_IMPORT.value
    )
    total_value_cad: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=4), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lines: Mapped[list["PortfolioReviewLine"]] = relationship(
        "PortfolioReviewLine",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="PortfolioReviewLine.sort_order",
    )

    __table_args__ = (
        UniqueConstraint("as_of_date", name="uq_portfolio_reviews_as_of_date"),
    )


class PortfolioReviewLine(Base):
    """Single Canadian holding row within a portfolio review."""

    __tablename__ = "portfolio_review_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_reviews.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    investment: Mapped[str] = mapped_column(String(512), nullable=False)
    platform: Mapped[str] = mapped_column(String(256), nullable=False, default="")

    value_cad: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=4), nullable=True
    )

    pct_global: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=6), nullable=True
    )
    return_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=6), nullable=True
    )
    div_per_year: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=18, scale=4), nullable=True
    )
    yield_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=6), nullable=True
    )

    target_pct: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    delta: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    conviction: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    raw_row: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    review: Mapped["PortfolioReview"] = relationship(
        "PortfolioReview", back_populates="lines"
    )
