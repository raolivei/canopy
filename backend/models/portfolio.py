"""Domain models for portfolio data."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Holding(BaseModel):
    """Represents a single holding position."""

    symbol: str
    name: str
    quantity: Decimal
    average_price: Decimal
    currency: str


class PortfolioSnapshot(BaseModel):
    """Portfolio state at a point in time."""

    as_of: datetime
    holdings: list[Holding] = []

