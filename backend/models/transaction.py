from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    BUY = "buy"  # Investment purchase
    SELL = "sell"  # Investment sale


class Transaction(BaseModel):
    id: int | None = None
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: str | None = None
    date: datetime
    account: str | None = None

    # Enhanced Monarch-like fields
    merchant: str | None = None  # Clean merchant name
    original_statement: str | None = None  # Raw bank statement text
    notes: str | None = None  # User notes
    tags: list[str] = Field(default_factory=list)  # Transaction tags

    # Investment-specific fields
    ticker: str | None = None  # Stock/ETF ticker symbol
    shares: float | None = None  # Number of shares
    price_per_share: float | None = None  # Price per share


class TransactionCreate(BaseModel):
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: str | None = None
    date: datetime | None = None
    account: str | None = None

    # Enhanced Monarch-like fields
    merchant: str | None = None
    original_statement: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Investment-specific fields
    ticker: str | None = None
    shares: float | None = None
    price_per_share: float | None = None
