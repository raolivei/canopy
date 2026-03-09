"""Transactions API endpoints for managing income, expenses, and transfers."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, desc, or_, extract, case

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
    search: Optional[str] = Query(None, description="Search description, merchant, notes"),
    category: Optional[str] = Query(None, description="Filter by category"),
    account: Optional[str] = Query(None, description="Filter by account"),
    type: Optional[str] = Query(None, description="Filter by type (income, expense, transfer)"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    min_amount: Optional[float] = Query(None, description="Minimum amount (absolute)"),
    max_amount: Optional[float] = Query(None, description="Maximum amount (absolute)"),
    import_source: Optional[str] = Query(None, description="Filter by import source"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum number of transactions"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Get all transactions with optional filters and currency conversion."""
    query = select(TransactionModel)
    
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                TransactionModel.description.ilike(term),
                TransactionModel.merchant.ilike(term),
                TransactionModel.notes.ilike(term),
                TransactionModel.category.ilike(term),
                TransactionModel.original_statement.ilike(term),
            )
        )
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
    if min_amount is not None:
        query = query.where(func.abs(TransactionModel.amount) >= Decimal(str(min_amount)))
    if max_amount is not None:
        query = query.where(func.abs(TransactionModel.amount) <= Decimal(str(max_amount)))
    if import_source:
        query = query.where(TransactionModel.import_source == import_source)
    
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


# ── Annual Report ──────────────────────────────────────────────────────────────

# Categories that represent internal money movement, not real income/spending
NOISE_INCOME_CATS = {
    "Transfer", "Credit Card Payment", "Loan Repayment",
    "Sell", "Returned Purchase",
}
NOISE_EXPENSE_CATS = {
    "Transfer", "Credit Card Payment", "Loan Repayment",
    "Reimbursement",
}
INVESTMENT_CATS = {"Buy", "Investments", "Sell"}


@router.get("/annual-report")
async def get_annual_report(
    db: DbSession,
    year: int = Query(..., description="Year for the report"),
):
    """Annual spending report with clean income/expense figures.

    Excludes internal transfers, credit card payments, and loan repayments
    to show real money in vs real money spent.
    """
    from sqlalchemy import text

    # Monthly summary
    monthly_rows = db.execute(text("""
        SELECT
            EXTRACT(MONTH FROM date)::int AS month,
            type,
            category,
            SUM(amount) AS total
        FROM transactions
        WHERE EXTRACT(YEAR FROM date) = :year
          AND type IN ('income', 'expense')
        GROUP BY month, type, category
    """), {"year": year}).fetchall()

    # Build monthly buckets
    months: dict[int, dict] = {
        m: {"month": m, "income": 0.0, "expenses": 0.0, "investments": 0.0}
        for m in range(1, 13)
    }
    category_totals: dict[str, float] = {}
    income_sources: dict[str, float] = {}

    for row in monthly_rows:
        m, typ, cat, total = row.month, row.type, row.category or "", float(row.total)
        if typ == "income":
            if cat not in NOISE_INCOME_CATS:
                months[m]["income"] += total
                income_sources[cat or "Uncategorized"] = income_sources.get(cat or "Uncategorized", 0) + total
        elif typ == "expense":
            if cat in INVESTMENT_CATS:
                months[m]["investments"] += total
            elif cat not in NOISE_EXPENSE_CATS:
                months[m]["expenses"] += total
                category_totals[cat or "Uncategorized"] = category_totals.get(cat or "Uncategorized", 0) + total

    # Summary totals
    total_income = sum(m["income"] for m in months.values())
    total_expenses = sum(m["expenses"] for m in months.values())
    total_investments = sum(m["investments"] for m in months.values())

    # Sorted category breakdown (top 15 for pie chart)
    sorted_cats = sorted(category_totals.items(), key=lambda x: -x[1])
    top_cats = sorted_cats[:15]
    other = sum(v for _, v in sorted_cats[15:])
    if other > 0:
        top_cats.append(("Other", other))

    # Top merchants
    merchant_rows = db.execute(text("""
        SELECT
            description,
            category,
            SUM(amount) AS total,
            COUNT(*) AS cnt
        FROM transactions
        WHERE EXTRACT(YEAR FROM date) = :year
          AND type = 'expense'
          AND (category IS NULL OR category NOT IN (
              'Transfer','Credit Card Payment','Loan Repayment',
              'Buy','Sell','Investments','Reimbursement'
          ))
        GROUP BY description, category
        ORDER BY total DESC
        LIMIT 20
    """), {"year": year}).fetchall()

    # Available years
    year_rows = db.execute(text("""
        SELECT DISTINCT EXTRACT(YEAR FROM date)::int AS y
        FROM transactions ORDER BY y DESC
    """)).fetchall()

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    return {
        "year": year,
        "available_years": [r.y for r in year_rows],
        "summary": {
            "real_income": round(total_income, 2),
            "real_expenses": round(total_expenses, 2),
            "investments": round(total_investments, 2),
            "net_savings": round(total_income - total_expenses, 2),
            "savings_rate": round((total_income - total_expenses) / total_income * 100, 1) if total_income > 0 else 0,
        },
        "by_month": [
            {
                "month": m,
                "month_name": month_names[m - 1],
                "income": round(months[m]["income"], 2),
                "expenses": round(months[m]["expenses"], 2),
                "investments": round(months[m]["investments"], 2),
                "net": round(months[m]["income"] - months[m]["expenses"], 2),
            }
            for m in range(1, 13)
        ],
        "by_category": [
            {"category": cat, "amount": round(amt, 2), "pct": round(amt / total_expenses * 100, 1) if total_expenses > 0 else 0}
            for cat, amt in top_cats
        ],
        "income_sources": [
            {"category": cat, "amount": round(amt, 2), "pct": round(amt / total_income * 100, 1) if total_income > 0 else 0}
            for cat, amt in sorted(income_sources.items(), key=lambda x: -x[1])
        ],
        "top_merchants": [
            {"description": r.description, "category": r.category or "", "total": round(float(r.total), 2), "count": r.cnt}
            for r in merchant_rows
        ],
    }
