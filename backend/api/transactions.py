from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from backend.models.transaction import Transaction, TransactionCreate, TransactionType
from backend.models.currency import convert_currency

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])

# In-memory storage for now (will be replaced with database later)
transactions_db: List[Transaction] = []
next_id = 1

@router.get("/", response_model=List[Transaction])
async def get_transactions(
    currency: Optional[str] = Query(None, description="Convert all amounts to this currency")
):
    """Get all transactions, optionally convert all amounts to a single currency"""
    if currency:
        # Convert all transactions to the requested currency
        converted_transactions = []
        for tx in transactions_db:
            converted_amount = convert_currency(tx.amount, tx.currency, currency.upper())
            # Use model_dump() for Pydantic v2, fallback to dict() for v1
            tx_dict = tx.model_dump() if hasattr(tx, 'model_dump') else tx.dict()
            converted_tx = Transaction(
                **tx_dict,
                amount=converted_amount,
                currency=currency.upper()
            )
            converted_transactions.append(converted_tx)
        return converted_transactions
    return transactions_db

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: int):
    """Get a specific transaction by ID"""
    for tx in transactions_db:
        if tx.id == transaction_id:
            return tx
    raise HTTPException(status_code=404, detail="Transaction not found")

@router.post("/", response_model=Transaction)
async def create_transaction(transaction: TransactionCreate):
    """Create a new transaction"""
    global next_id
    new_transaction = Transaction(
        id=next_id,
        description=transaction.description,
        amount=transaction.amount,
        currency=transaction.currency,
        type=transaction.type,
        category=transaction.category,
        date=transaction.date or datetime.now(),
        account=transaction.account,
    )
    next_id += 1
    transactions_db.append(new_transaction)
    return new_transaction

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int):
    """Delete a transaction"""
    global transactions_db
    for i, tx in enumerate(transactions_db):
        if tx.id == transaction_id:
            transactions_db.pop(i)
            return {"message": "Transaction deleted"}
    raise HTTPException(status_code=404, detail="Transaction not found")

