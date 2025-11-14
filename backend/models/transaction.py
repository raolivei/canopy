from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    BUY = "buy"  # Investment purchase
    SELL = "sell"  # Investment sale

class Transaction(BaseModel):
    id: Optional[int] = None
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: Optional[str] = None
    date: datetime
    account: Optional[str] = None
    
    # Enhanced Monarch-like fields
    merchant: Optional[str] = None  # Clean merchant name
    original_statement: Optional[str] = None  # Raw bank statement text
    notes: Optional[str] = None  # User notes
    tags: List[str] = Field(default_factory=list)  # Transaction tags
    
    # Investment-specific fields
    ticker: Optional[str] = None  # Stock/ETF ticker symbol
    shares: Optional[float] = None  # Number of shares
    price_per_share: Optional[float] = None  # Price per share

class TransactionCreate(BaseModel):
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: Optional[str] = None
    date: Optional[datetime] = None
    account: Optional[str] = None
    
    # Enhanced Monarch-like fields
    merchant: Optional[str] = None
    original_statement: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Investment-specific fields
    ticker: Optional[str] = None
    shares: Optional[float] = None
    price_per_share: Optional[float] = None

