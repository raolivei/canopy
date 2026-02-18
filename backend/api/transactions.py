"""Transactions API endpoints for managing income, expenses, and transfers."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, desc

from backend.db.session import DbSession
from backend.db.models.transaction import Transaction as TransactionModel
from backend.models.transaction import Transaction, TransactionCreate, TransactionType
from backend.models.currency import convert_currency

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])


def _db_to_response(tx: TransactionModel) -> Transaction:
    """Convert database model to response model."""
    return Transaction(
        id=tx.id,
        description=tx.description,
        amount=float(tx.amount),
        currency=tx.currency,
        type=TransactionType(tx.type),  # String to enum
        category=tx.category,
        date=tx.date,
        account=tx.account,
        merchant=tx.merchant,
        original_statement=tx.original_statement,
        notes=tx.notes,
        tags=tx.tags or [],
        ticker=tx.ticker,
    )


@router.get("/", response_model=list[Transaction])
async def get_transactions(
    db: DbSession,
    currency: Optional[str] = Query(None, description="Convert all amounts to this currency"),
    category: Optional[str] = Query(None, description="Filter by category"),
    account: Optional[str] = Query(None, description="Filter by account"),
    type: Optional[str] = Query(None, description="Filter by type (income, expense, transfer)"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum number of transactions"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Get all transactions with optional filters and currency conversion."""
    query = select(TransactionModel)
    
    # Apply filters
    if category:
        query = query.where(TransactionModel.category == category)
    if account:
        query = query.where(TransactionModel.account.ilike(f"%{account}%"))
    if type:
        query = query.where(TransactionModel.type == type)
    if start_date:
        query = query.where(TransactionModel.date >= start_date)
    if end_date:
        query = query.where(TransactionModel.date <= end_date)
    
    # Order by date descending (most recent first)
    query = query.order_by(desc(TransactionModel.date)).offset(offset).limit(limit)
    
    transactions = db.execute(query).scalars().all()
    
    result = []
    for tx in transactions:
        response = _db_to_response(tx)
        if currency:
            # Convert to requested currency
            converted_amount = convert_currency(float(tx.amount), tx.currency, currency.upper())
            response.amount = converted_amount
            response.currency = currency.upper()
        result.append(response)
    
    return result


@router.get("/summary")
async def get_transactions_summary(
    db: DbSession,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """Get summary statistics for transactions."""
    base_query = select(TransactionModel)
    
    if start_date:
        base_query = base_query.where(TransactionModel.date >= start_date)
    if end_date:
        base_query = base_query.where(TransactionModel.date <= end_date)
    
    transactions = db.execute(base_query).scalars().all()
    
    total_income = sum(float(t.amount) for t in transactions if t.type == "income")
    total_expenses = sum(float(t.amount) for t in transactions if t.type == "expense")
    total_transfers = sum(float(t.amount) for t in transactions if t.type == "transfer")
    
    # Group by category
    categories = {}
    for t in transactions:
        if t.type == "expense" and t.category:
            categories[t.category] = categories.get(t.category, 0) + float(t.amount)
    
    return {
        "total_transactions": len(transactions),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_transfers": total_transfers,
        "net": total_income - total_expenses,
        "by_category": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
    }


@router.get("/categories")
async def get_categories(db: DbSession):
    """Get list of all unique categories."""
    query = select(TransactionModel.category).where(
        TransactionModel.category.isnot(None)
    ).distinct()
    
    categories = db.execute(query).scalars().all()
    return sorted([c for c in categories if c])


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: int, db: DbSession):
    """Get a specific transaction by ID."""
    tx = db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    ).scalar_one_or_none()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return _db_to_response(tx)


@router.post("/", response_model=Transaction)
async def create_transaction(transaction: TransactionCreate, db: DbSession):
    """Create a new transaction."""
    new_tx = TransactionModel(
        description=transaction.description,
        amount=Decimal(str(transaction.amount)),
        currency=transaction.currency,
        type=transaction.type.value,
        date=transaction.date or datetime.now(),
        category=transaction.category,
        account=transaction.account,
        merchant=transaction.merchant,
        original_statement=transaction.original_statement,
        notes=transaction.notes,
        tags=transaction.tags,
        ticker=transaction.ticker,
    )
    
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    
    return _db_to_response(new_tx)


@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    transaction: TransactionCreate,
    db: DbSession
):
    """Update an existing transaction."""
    tx = db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    ).scalar_one_or_none()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx.description = transaction.description
    tx.amount = Decimal(str(transaction.amount))
    tx.currency = transaction.currency
    tx.type = DbTransactionType(transaction.type.value)
    tx.date = transaction.date or tx.date
    tx.category = transaction.category
    tx.account = transaction.account
    tx.merchant = transaction.merchant
    tx.original_statement = transaction.original_statement
    tx.notes = transaction.notes
    tx.tags = transaction.tags
    tx.ticker = transaction.ticker
    
    db.commit()
    db.refresh(tx)
    
    return _db_to_response(tx)


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: DbSession):
    """Delete a transaction."""
    tx = db.execute(
        select(TransactionModel).where(TransactionModel.id == transaction_id)
    ).scalar_one_or_none()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(tx)
    db.commit()
    
    return {"message": "Transaction deleted"}


@router.delete("/")
async def delete_all_transactions(
    db: DbSession,
    confirm: bool = Query(False, description="Must be true to confirm deletion")
):
    """Delete all transactions. Requires confirmation."""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to delete all transactions"
        )
    
    count = db.execute(select(func.count(TransactionModel.id))).scalar()
    db.execute(select(TransactionModel).delete())
    db.commit()
    
    return {"message": f"Deleted {count} transactions"}
