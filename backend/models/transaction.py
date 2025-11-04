from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class Transaction(BaseModel):
    id: Optional[int] = None
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: Optional[str] = None
    date: datetime
    account: Optional[str] = None

class TransactionCreate(BaseModel):
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: Optional[str] = None
    date: Optional[datetime] = None
    account: Optional[str] = None

