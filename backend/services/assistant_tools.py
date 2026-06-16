"""Modular assistant tools — each tool is a standalone function.

Simplifies AssistantService by extracting tool implementations into
composable functions with consistent signatures.
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Any, Protocol
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction
from backend.db.models.asset import Asset


class ToolFunction(Protocol):
    """Protocol for assistant tool functions."""
    def __call__(self, db: Session, **kwargs) -> dict[str, Any]: ...


def _date_range(months: int = 1) -> tuple[date, date]:
    """Get date range for last N months."""
    today = datetime.now().date()
    return today - timedelta(days=30 * months), today


def _transactions_in_range(
    db: Session,
    start: date,
    end: date,
    tx_type: str | None = None,
    **filters
) -> list[Transaction]:
    """Query transactions with common filters."""
    query = select(Transaction).where(Transaction.date.between(start, end))
    if tx_type:
        query = query.where(Transaction.type == tx_type)
    for key, value in filters.items():
        if value is not None:
            query = query.where(getattr(Transaction, key) == value)
    return db.execute(query).scalars().all()


def budget_status(db: Session, month: str | None = None) -> dict[str, Any]:
    """Current vs target budget, month progress, alerts."""
    # Stub - would query Budget model when implemented
    return {
        "month": month or datetime.now().strftime("%Y-%m"),
        "status": "no_budgets_configured",
        "message": "Budget tracking not yet configured"
    }


def cashflow_summary(db: Session, month: str | None = None) -> dict[str, Any]:
    """Income/expense/savings summary for current or specified month."""
    target_month = datetime.strptime(month, "%Y-%m").date() if month else datetime.now().date()
    start = date(target_month.year, target_month.month, 1)

    # Calculate end date (last day of month)
    if target_month.month == 12:
        end = date(target_month.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(target_month.year, target_month.month + 1, 1) - timedelta(days=1)

    txns = _transactions_in_range(db, start, end)

    income = sum(float(tx.amount) for tx in txns if tx.type == "income")
    expenses = sum(float(abs(tx.amount)) for tx in txns if tx.type == "expense")
    savings = income - expenses
    savings_rate = (savings / income * 100) if income > 0 else 0

    return {
        "month": start.strftime("%Y-%m"),
        "income": income,
        "expenses": expenses,
        "savings": savings,
        "savings_rate": round(savings_rate, 2)
    }


def recurring_analysis(db: Session, months: int = 3) -> dict[str, Any]:
    """Upcoming subscriptions, payment dates, frequency analysis."""
    start, end = _date_range(months)
    txns = _transactions_in_range(db, start, end, tx_type="expense")

    # Group by merchant
    merchant_dates = defaultdict(list)
    for tx in txns:
        if tx.merchant:
            merchant_dates[tx.merchant].append((tx.date, float(abs(tx.amount))))

    # Detect recurring patterns (≥3 transactions, roughly monthly)
    recurring = []
    for merchant, dates_amounts in merchant_dates.items():
        if len(dates_amounts) < 3:
            continue

        dates = sorted([d for d, _ in dates_amounts])
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_interval = sum(intervals) / len(intervals)

        # Monthly pattern: 25-35 day intervals
        if 25 <= avg_interval <= 35:
            amounts = [amt for _, amt in dates_amounts]
            avg_amount = sum(amounts) / len(amounts)
            next_date = dates[-1] + timedelta(days=int(avg_interval))

            recurring.append({
                "merchant": merchant,
                "avg_interval_days": round(avg_interval, 1),
                "avg_amount": round(avg_amount, 2),
                "last_payment": dates[-1].isoformat(),
                "predicted_next": next_date.isoformat(),
                "confidence": min(0.9, len(dates_amounts) / 12),  # Higher confidence with more data
            })

    return {
        "analysis_months": months,
        "recurring_found": len(recurring),
        "subscriptions": sorted(recurring, key=lambda x: x["avg_amount"], reverse=True)
    }


def spending_patterns(db: Session, months: int = 3) -> dict[str, Any]:
    """Top categories, trends, anomalies."""
    start, end = _date_range(months)
    txns = _transactions_in_range(db, start, end, tx_type="expense")

    # Group by category and month
    monthly_totals = defaultdict(lambda: defaultdict(float))
    for tx in txns:
        month_key = tx.date.strftime("%Y-%m")
        category = tx.category or "Uncategorized"
        monthly_totals[month_key][category] += float(abs(tx.amount))

    # Calculate trends
    category_trends = {}
    all_categories = set().union(*[set(m.keys()) for m in monthly_totals.values()])

    for category in all_categories:
        months_data = sorted([
            (month, monthly_totals[month].get(category, 0))
            for month in sorted(monthly_totals.keys())
        ])

        if len(months_data) >= 2:
            prev, curr = months_data[-2][1], months_data[-1][1]
            change_pct = ((curr - prev) / prev * 100) if prev > 0 else None

            category_trends[category] = {
                "category": category,
                "current": curr,
                "previous": prev,
                "trend": "up" if change_pct and change_pct > 5 else "down" if change_pct and change_pct < -5 else "stable",
                "change_percent": change_pct
            }

    sorted_trends = sorted(category_trends.values(), key=lambda x: x["current"], reverse=True)[:10]
    total = sum(float(abs(tx.amount)) for tx in txns)

    return {
        "analysis_months": months,
        "top_categories": sorted_trends,
        "total_spending": round(total, 2),
        "average_monthly": round(total / max(months, 1), 2)
    }


def merchant_insights(db: Session, months: int = 3, top_n: int = 10) -> dict[str, Any]:
    """Frequent merchants, spending by merchant."""
    start, end = _date_range(months)
    txns = _transactions_in_range(db, start, end, tx_type="expense")
    txns = [tx for tx in txns if tx.merchant]  # Filter for merchants only

    # Group by merchant
    merchant_stats = defaultdict(lambda: {"total": 0, "count": 0, "amounts": []})
    for tx in txns:
        stats = merchant_stats[tx.merchant]
        stats["total"] += float(abs(tx.amount))
        stats["count"] += 1
        stats["amounts"].append(float(abs(tx.amount)))

    merchants = [
        {
            "merchant": name,
            "total_spent": round(stats["total"], 2),
            "transaction_count": stats["count"],
            "average_transaction": round(stats["total"] / stats["count"], 2),
            "frequency": "monthly" if stats["count"] / months >= 1 else "occasional"
        }
        for name, stats in merchant_stats.items()
    ]

    sorted_merchants = sorted(merchants, key=lambda x: x["total_spent"], reverse=True)[:top_n]

    return {
        "analysis_months": months,
        "top_merchants": sorted_merchants,
        "total_unique_merchants": len(merchant_stats)
    }


def goal_progress(db: Session) -> dict[str, Any]:
    """Savings goals, net worth targets, FIRE timeline."""
    # Stub - would integrate with portfolio calculator
    return {
        "status": "not_configured",
        "message": "Goal tracking not yet configured"
    }


# Tool registry for dynamic discovery
ASSISTANT_TOOLS: dict[str, ToolFunction] = {
    "budget_status": budget_status,
    "cashflow_summary": cashflow_summary,
    "recurring_analysis": recurring_analysis,
    "spending_patterns": spending_patterns,
    "merchant_insights": merchant_insights,
    "goal_progress": goal_progress,
}
