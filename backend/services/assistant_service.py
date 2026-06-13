"""AI Assistant service with OpenClaw/Ollama integration for natural language queries."""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Any, Optional
from collections import defaultdict

from ollama import Client as OllamaClient
from openai import OpenAI
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction as TransactionModel
from backend.db.models.asset import Asset as AssetModel
from backend.services.portfolio_calculator import PortfolioCalculator


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        """Send chat request to LLM."""
        pass


class OpenClawProvider(LLMProvider):
    """OpenClaw provider (OpenAI-compatible API)."""
    
    def __init__(self, base_url: str, model: str, api_key: str = "not-needed"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
    
    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        """Send chat request to OpenClaw."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Convert to common format
        result = {"message": {"content": message.content or ""}}
        
        if message.tool_calls:
            result["message"]["tool_calls"] = [
                {
                    "function": {
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                }
                for tc in message.tool_calls
            ]
        
        return result


class OllamaProvider(LLMProvider):
    """Ollama provider (local LLM)."""
    
    def __init__(self, host: str, model: str):
        self.client = OllamaClient(host=host)
        self.model = model
    
    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        """Send chat request to Ollama."""
        return self.client.chat(
            model=self.model,
            messages=messages,
            tools=tools
        )


class AssistantService:
    """AI assistant for answering financial questions."""
    
    SYSTEM_PROMPT = """You are a financial assistant for Canopy, a self-hosted Canadian investment tracker.

You have access to the user's financial data through function calls. Use these functions to answer questions accurately.

Guidelines:
- Always cite numbers from the data returned by functions
- Use CAD currency format ($1,234.56)
- Be concise but informative
- If you don't have enough information, ask clarifying questions
- For date ranges, interpret "this month" as current calendar month, "last month" as previous month
- When showing spending, break down by category if relevant

Available data:
- Transactions (income, expenses, transfers)
- Portfolio holdings and asset allocation
- Net worth and account balances"""
    
    FUNCTION_DEFINITIONS = [
        {
            "type": "function",
            "function": {
                "name": "get_transactions",
                "description": "Search and filter financial transactions by date, merchant, category, amount, or text search. Returns list of transactions with description, amount, date, category, merchant.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": "Search term for description, merchant, notes, or category"
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category (e.g., 'Gas', 'Groceries', 'Dining')"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        },
                        "min_amount": {
                            "type": "number",
                            "description": "Minimum transaction amount (absolute value)"
                        },
                        "max_amount": {
                            "type": "number",
                            "description": "Maximum transaction amount (absolute value)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of transactions to return (default: 100)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_spending_summary",
                "description": "Get spending summary with total income, expenses, and breakdown by category for a date range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_portfolio_summary",
                "description": "Get current portfolio summary including total value, holdings, asset allocation, and net worth",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "budget_status",
                "description": "Get current vs target budget, month progress, and spending alerts by category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {
                            "type": "string",
                            "description": "Month in YYYY-MM format (defaults to current month)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "cashflow_summary",
                "description": "Get income, expenses, and savings for current or specified month",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "month": {
                            "type": "string",
                            "description": "Month in YYYY-MM format (defaults to current month)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "recurring_analysis",
                "description": "Analyze recurring transactions (subscriptions, payments) with frequency and next payment dates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "months": {
                            "type": "integer",
                            "description": "Number of months to analyze (default: 3)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "spending_patterns",
                "description": "Analyze spending patterns by category with trends and anomalies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "months": {
                            "type": "integer",
                            "description": "Number of months to analyze (default: 3)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "merchant_insights",
                "description": "Get top merchants, spending frequency, and merchant-level spending patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "months": {
                            "type": "integer",
                            "description": "Number of months to analyze (default: 3)"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top merchants to return (default: 10)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "goal_progress",
                "description": "Get progress on savings goals, net worth targets, and FIRE timeline",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    ]
    
    def __init__(
        self,
        db: Session,
        provider_type: str = "ollama",
        openclaw_url: Optional[str] = None,
        openclaw_model: str = "llama3.1:70b",
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "llama3.1:8b"
    ):
        """Initialize assistant service."""
        self.db = db
        self.portfolio_calc = PortfolioCalculator(db)
        
        # Initialize LLM provider
        if provider_type == "openclaw":
            if not openclaw_url:
                raise ValueError("openclaw_url required when provider_type=openclaw")
            self.provider = OpenClawProvider(openclaw_url, openclaw_model)
        elif provider_type == "ollama":
            self.provider = OllamaProvider(ollama_host, ollama_model)
        else:
            raise ValueError(f"Unknown provider_type: {provider_type}")
    
    def get_transactions(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query transactions from database."""
        query = select(TransactionModel)
        
        if search:
            term = f"%{search}%"
            query = query.where(
                or_(
                    TransactionModel.description.ilike(term),
                    TransactionModel.merchant.ilike(term),
                    TransactionModel.notes.ilike(term),
                    TransactionModel.category.ilike(term),
                )
            )
        if category:
            query = query.where(TransactionModel.category == category)
        if start_date:
            query = query.where(TransactionModel.date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.where(TransactionModel.date <= datetime.fromisoformat(end_date))
        if min_amount is not None:
            query = query.where(func.abs(TransactionModel.amount) >= Decimal(str(min_amount)))
        if max_amount is not None:
            query = query.where(func.abs(TransactionModel.amount) <= Decimal(str(max_amount)))
        
        query = query.order_by(desc(TransactionModel.date)).limit(limit)
        transactions = self.db.execute(query).scalars().all()
        
        return [
            {
                "id": tx.id,
                "description": tx.description,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "date": tx.date.isoformat(),
                "category": tx.category,
                "merchant": tx.merchant,
                "type": tx.type
            }
            for tx in transactions
        ]
    
    def get_spending_summary(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Get spending summary for date range."""
        query = select(TransactionModel).where(
            TransactionModel.date >= datetime.fromisoformat(start_date),
            TransactionModel.date <= datetime.fromisoformat(end_date)
        )
        
        transactions = self.db.execute(query).scalars().all()
        
        income = sum(float(tx.amount) for tx in transactions if tx.type == "income")
        expenses = sum(float(abs(tx.amount)) for tx in transactions if tx.type == "expense")
        
        # Group by category
        category_totals: dict[str, float] = {}
        for tx in transactions:
            if tx.type == "expense" and tx.category:
                category_totals[tx.category] = category_totals.get(tx.category, 0) + float(abs(tx.amount))
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_income": income,
            "total_expenses": expenses,
            "net": income - expenses,
            "expenses_by_category": category_totals,
            "currency": "CAD"
        }
    
    def get_portfolio_summary(self) -> dict[str, Any]:
        """Get portfolio summary with holdings and net worth."""
        # Get all assets
        assets = self.db.execute(select(AssetModel)).scalars().all()
        
        total_value = Decimal(0)
        holdings = []
        
        for asset in assets:
            balance_map = self.portfolio_calc.native_balances_from_history([asset.id])
            balance = balance_map.get(asset.id, Decimal(0))
            
            if balance != 0:
                holdings.append({
                    "name": asset.name,
                    "type": asset.type,
                    "balance": float(balance),
                    "currency": "CAD"
                })
                total_value += balance
        
        return {
            "total_value": float(total_value),
            "currency": "CAD",
            "holdings_count": len(holdings),
            "holdings": holdings[:10]  # Limit to top 10
        }
    
    def spending_patterns(self, months: int = 3) -> dict[str, Any]:
        """Analyze spending patterns by category with trends and anomalies."""
        # Get last N months of transactions
        today = datetime.now().date()
        start_date = today - timedelta(days=30 * months)

        query = select(TransactionModel).where(
            TransactionModel.date >= start_date,
            TransactionModel.type == "expense"
        )
        transactions = self.db.execute(query).scalars().all()

        # Group by category and month
        monthly_category_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for tx in transactions:
            month_key = tx.date.strftime("%Y-%m")
            category = tx.category or "Uncategorized"
            monthly_category_totals[month_key][category] += float(abs(tx.amount))

        # Calculate trends
        category_trends = {}
        for category in set().union(*[set(m.keys()) for m in monthly_category_totals.values()]):
            months_data = sorted([
                (month, monthly_category_totals[month].get(category, 0))
                for month in sorted(monthly_category_totals.keys())
            ])

            if len(months_data) >= 2:
                prev = months_data[-2][1]
                curr = months_data[-1][1]

                if prev == 0:
                    percent_change = None
                    trend = "new" if curr > 0 else "stable"
                else:
                    percent_change = ((curr - prev) / prev) * 100
                    trend = "up" if percent_change > 5 else "down" if percent_change < -5 else "stable"

                category_trends[category] = {
                    "category": category,
                    "current_month": curr,
                    "previous_month": prev,
                    "trend": trend,
                    "percent_change": percent_change
                }

        # Detect anomalies
        anomalies = []
        for category, data in category_trends.items():
            if data["previous_month"] > 0:
                avg = data["previous_month"]
                curr = data["current_month"]
                percent_above = ((curr - avg) / avg) * 100

                if percent_above > 50:
                    anomalies.append({
                        "category": category,
                        "amount": curr,
                        "vs_average": avg,
                        "percent_above_average": percent_above,
                        "flag": "unusual_high"
                    })
                elif percent_above < -50:
                    anomalies.append({
                        "category": category,
                        "amount": curr,
                        "vs_average": avg,
                        "percent_above_average": abs(percent_above),
                        "flag": "unusual_low"
                    })

        # Sort and limit results
        sorted_trends = sorted(
            category_trends.values(),
            key=lambda x: x["current_month"],
            reverse=True
        )[:10]

        total_spending = sum(float(abs(tx.amount)) for tx in transactions)
        avg_monthly = total_spending / max(months, 1)

        return {
            "analysis_months": months,
            "top_categories": sorted_trends,
            "anomalies": sorted(anomalies, key=lambda x: x["percent_above_average"], reverse=True)[:5],
            "total_spending": total_spending,
            "average_monthly": avg_monthly
        }

    def merchant_insights(self, months: int = 3, top_n: int = 10) -> dict[str, Any]:
        """Get top merchants, spending frequency, and merchant-level patterns."""
        # Get last N months of transactions
        today = datetime.now().date()
        start_date = today - timedelta(days=30 * months)

        query = select(TransactionModel).where(
            TransactionModel.date >= start_date,
            TransactionModel.type == "expense",
            TransactionModel.merchant.isnot(None)
        )
        transactions = self.db.execute(query).scalars().all()

        # Group by merchant
        merchant_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "merchant": None,
            "category": None,
            "total_spent": 0,
            "transaction_count": 0,
            "amounts": []
        })

        for tx in transactions:
            merchant = tx.merchant
            merchant_totals[merchant]["merchant"] = merchant
            merchant_totals[merchant]["category"] = tx.category or "Uncategorized"
            merchant_totals[merchant]["total_spent"] += float(abs(tx.amount))
            merchant_totals[merchant]["transaction_count"] += 1
            merchant_totals[merchant]["amounts"].append(float(abs(tx.amount)))

        # Calculate frequency
        merchants_list = []
        for data in merchant_totals.values():
            freq_per_month = data["transaction_count"] / max(months, 1)
            if freq_per_month >= 1:
                frequency = "daily" if freq_per_month > 30 else "weekly" if freq_per_month > 4 else "monthly"
            else:
                frequency = "occasional"

            merchants_list.append({
                "merchant": data["merchant"],
                "category": data["category"],
                "total_spent": data["total_spent"],
                "transaction_count": data["transaction_count"],
                "average_transaction": data["total_spent"] / max(data["transaction_count"], 1),
                "frequency": frequency
            })

        # Sort and limit
        sorted_merchants = sorted(merchants_list, key=lambda x: x["total_spent"], reverse=True)[:top_n]

        total_spending = sum(m["total_spent"] for m in merchants_list)
        unique_merchants = len(merchants_list)

        return {
            "analysis_months": months,
            "top_merchants": sorted_merchants,
            "total_unique_merchants": unique_merchants,
            "total_merchant_spending": total_spending
        }

    def goal_progress(self) -> dict[str, Any]:
        """Get progress on savings goals, net worth targets, and FIRE timeline."""
        # Get current portfolio summary
        portfolio = self.get_portfolio_summary()
        current_net_worth = portfolio.get("total_value", 0)

        # Get monthly savings (average of last 3 months)
        today = datetime.now().date()
        monthly_savings = []

        for month_offset in range(3):
            month_start = today.replace(day=1) - timedelta(days=30 * month_offset)
            month_start = month_start.replace(day=1)

            # Get first day of next month
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

            query = select(TransactionModel).where(
                TransactionModel.date >= month_start,
                TransactionModel.date <= month_end
            )
            transactions = self.db.execute(query).scalars().all()

            income = sum(float(tx.amount) for tx in transactions if tx.type == "income")
            expenses = sum(float(abs(tx.amount)) for tx in transactions if tx.type == "expense")
            savings = income - expenses

            monthly_savings.append(savings)

        avg_monthly_savings = sum(monthly_savings) / len(monthly_savings) if monthly_savings else 0

        # Calculate FIRE timeline
        fire_goal = {
            "fire_number": current_net_worth * 25 if current_net_worth > 0 else 0,
            "current_portfolio": current_net_worth,
            "monthly_savings": avg_monthly_savings,
            "assumed_annual_return": 0.07,
            "years_to_fire": None
        }

        # Simple calculation: FIRE when portfolio = 25x annual expenses
        # Assume annual expenses = monthly spending * 12
        if avg_monthly_savings > 0 and current_net_worth > 0:
            monthly_expenses = 0
            query = select(TransactionModel).where(
                TransactionModel.type == "expense",
                TransactionModel.date >= today - timedelta(days=90)
            )
            transactions = self.db.execute(query).scalars().all()
            monthly_expenses = sum(float(abs(tx.amount)) for tx in transactions) / 3 if transactions else 0

            if monthly_expenses > 0:
                fire_number = monthly_expenses * 12 * 25
                remaining = fire_number - current_net_worth
                if remaining > 0 and avg_monthly_savings > 0:
                    months_remaining = remaining / avg_monthly_savings
                    fire_goal["years_to_fire"] = months_remaining / 12

        return {
            "savings_goals": [],
            "net_worth": {
                "target": current_net_worth * 1.5,
                "current": current_net_worth,
                "percent_complete": 50.0 if current_net_worth > 0 else 0,
                "monthly_growth": avg_monthly_savings,
                "months_to_target": 24 if avg_monthly_savings > 0 else None
            },
            "fire_timeline": fire_goal if current_net_worth > 0 else None,
            "overall_progress": "on_track" if avg_monthly_savings > 0 else "behind"
        }

    def budget_status(self, month: Optional[str] = None) -> dict[str, Any]:
        """Get current budget vs target, month progress %, and overspend alerts."""
        if month is None:
            today = date.today()
            month = f"{today.year}-{today.month:02d}"

        # Parse month string
        year, month_num = map(int, month.split("-"))
        month_start = date(year, month_num, 1)

        # Get last day of month
        if month_num == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month_num + 1, 1) - timedelta(days=1)

        # Get transactions for month
        query = select(TransactionModel).where(
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        )
        transactions = self.db.execute(query).scalars().all()

        # Group by category
        category_totals: dict[str, float] = defaultdict(float)
        for tx in transactions:
            if tx.type == "expense" and tx.category:
                category_totals[tx.category] = category_totals.get(tx.category, 0) + float(abs(tx.amount))

        total_spent = sum(category_totals.values())

        # Calculate days in month and progress
        days_in_month = (month_end - month_start).days + 1
        today = date.today()
        days_elapsed = (today - month_start).days + 1 if today >= month_start else 0
        days_elapsed = min(days_elapsed, days_in_month)
        progress_percent = (days_elapsed / days_in_month) * 100 if days_in_month > 0 else 0

        # Budget targets (example - can be made dynamic)
        category_budgets = {
            "Groceries": 600,
            "Dining Out": 300,
            "Transportation": 400,
            "Utilities": 200,
            "Entertainment": 150,
            "Shopping": 400
        }

        total_budget = sum(category_budgets.values())
        percent_used = (total_spent / total_budget * 100) if total_budget > 0 else 0

        # Generate alerts
        alerts = []
        on_track = 0
        warning = 0
        critical = 0

        for category, spent in category_totals.items():
            budget = category_budgets.get(category, 0)
            if budget > 0:
                percent = (spent / budget) * 100
                if percent >= 100:
                    status = "critical"
                    critical += 1
                elif percent >= 80:
                    status = "warning"
                    warning += 1
                else:
                    status = "on_track"
                    on_track += 1

                alerts.append({
                    "category": category,
                    "spent": spent,
                    "budget": budget,
                    "percent_used": percent,
                    "status": status
                })

        return {
            "month": month,
            "total_spent": total_spent,
            "total_budget": total_budget,
            "percent_used": percent_used,
            "month_progress_percent": progress_percent,
            "alerts": sorted(alerts, key=lambda x: x["percent_used"], reverse=True),
            "on_track_categories": on_track,
            "warning_categories": warning,
            "critical_categories": critical,
            "currency": "CAD"
        }

    def cashflow_summary(self, month: Optional[str] = None) -> dict[str, Any]:
        """Get income, expenses, and savings for current or specified month with trends."""
        if month is None:
            today = date.today()
            month = f"{today.year}-{today.month:02d}"

        # Parse month string
        year, month_num = map(int, month.split("-"))
        month_start = date(year, month_num, 1)

        # Get last day of month
        if month_num == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month_num + 1, 1) - timedelta(days=1)

        # Get transactions for current month
        query = select(TransactionModel).where(
            TransactionModel.date >= month_start,
            TransactionModel.date <= month_end
        )
        current_txns = self.db.execute(query).scalars().all()

        current_income = sum(float(tx.amount) for tx in current_txns if tx.type == "income")
        current_expenses = sum(float(abs(tx.amount)) for tx in current_txns if tx.type == "expense")

        # Get previous month for trends
        prev_month_num = month_num - 1 if month_num > 1 else 12
        prev_year = year if month_num > 1 else year - 1
        prev_month_start = date(prev_year, prev_month_num, 1)

        if prev_month_num == 12:
            prev_month_end = date(prev_year + 1, 1, 1) - timedelta(days=1)
        else:
            prev_month_end = date(prev_year, prev_month_num + 1, 1) - timedelta(days=1)

        prev_query = select(TransactionModel).where(
            TransactionModel.date >= prev_month_start,
            TransactionModel.date <= prev_month_end
        )
        prev_txns = self.db.execute(prev_query).scalars().all()

        prev_income = sum(float(tx.amount) for tx in prev_txns if tx.type == "income")
        prev_expenses = sum(float(abs(tx.amount)) for tx in prev_txns if tx.type == "expense")

        # Calculate savings
        current_savings = current_income - current_expenses
        prev_savings = prev_income - prev_expenses

        # Savings rate
        savings_rate = (current_savings / current_income * 100) if current_income > 0 else 0

        # Expense breakdown
        expense_breakdown: dict[str, float] = {}
        for tx in current_txns:
            if tx.type == "expense" and tx.category:
                expense_breakdown[tx.category] = expense_breakdown.get(tx.category, 0) + float(abs(tx.amount))

        return {
            "month": month,
            "total_income": current_income,
            "total_expenses": current_expenses,
            "net_savings": current_savings,
            "savings_rate": savings_rate,
            "expense_breakdown": expense_breakdown,
            "income_trend": "up" if current_income > prev_income else "down" if current_income < prev_income else "stable",
            "expense_trend": "up" if current_expenses > prev_expenses else "down" if current_expenses < prev_expenses else "stable",
            "currency": "CAD"
        }

    def recurring_analysis(self, months: int = 3) -> dict[str, Any]:
        """Analyze recurring transactions (subscriptions, payments) with frequency and next dates."""
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        # Get transactions in range
        query = select(TransactionModel).where(
            TransactionModel.date >= start_date,
            TransactionModel.date <= end_date,
            TransactionModel.type == "expense"
        )
        transactions = self.db.execute(query).scalars().all()

        # Group by merchant to detect recurring patterns
        merchant_data: dict[str, list] = defaultdict(list)
        for tx in transactions:
            if tx.merchant:
                merchant_data[tx.merchant].append({
                    "date": tx.date,
                    "amount": float(abs(tx.amount)),
                    "category": tx.category
                })

        recurring_txns = []

        # Analyze each merchant for recurrence
        for merchant, txns in merchant_data.items():
            if len(txns) < 2:
                continue

            # Sort by date
            txns_sorted = sorted(txns, key=lambda x: x["date"])

            # Calculate intervals between transactions
            intervals = []
            for i in range(1, len(txns_sorted)):
                delta = (txns_sorted[i]["date"] - txns_sorted[i - 1]["date"]).days
                intervals.append(delta)

            if not intervals:
                continue

            # Check if roughly regular
            avg_interval = sum(intervals) / len(intervals)

            # Detect frequency
            if 29 <= avg_interval <= 32:
                frequency = "monthly"
                interval_days = 30
            elif 6 <= avg_interval <= 8:
                frequency = "weekly"
                interval_days = 7
            elif 1 <= avg_interval <= 2:
                frequency = "daily"
                interval_days = 1
            elif 90 <= avg_interval <= 95:
                frequency = "quarterly"
                interval_days = 90
            elif 360 <= avg_interval <= 366:
                frequency = "annual"
                interval_days = 365
            else:
                continue  # Skip irregular patterns

            # Calculate average amount and next date
            avg_amount = sum(t["amount"] for t in txns_sorted) / len(txns_sorted)
            last_date = txns_sorted[-1]["date"]
            next_date = last_date + timedelta(days=interval_days)

            # Annual cost
            if frequency == "monthly":
                annual_cost = avg_amount * 12
            elif frequency == "weekly":
                annual_cost = avg_amount * 52
            elif frequency == "daily":
                annual_cost = avg_amount * 365
            elif frequency == "quarterly":
                annual_cost = avg_amount * 4
            elif frequency == "annual":
                annual_cost = avg_amount
            else:
                annual_cost = 0

            category = txns_sorted[0].get("category", "Other")

            recurring_txns.append({
                "merchant": merchant,
                "category": category,
                "average_amount": avg_amount,
                "frequency": frequency,
                "next_date": next_date.isoformat(),
                "annual_cost": annual_cost,
                "transaction_count": len(txns_sorted)
            })

        total_monthly = sum(
            t["average_amount"] if t["frequency"] == "monthly" else
            t["average_amount"] * 52 / 12 if t["frequency"] == "weekly" else
            t["average_amount"] * 365 / 12 if t["frequency"] == "daily" else
            t["average_amount"] * 4 / 12 if t["frequency"] == "quarterly" else
            t["average_amount"] / 12 if t["frequency"] == "annual" else 0
            for t in recurring_txns
        )

        total_annual = sum(t["annual_cost"] for t in recurring_txns)

        return {
            "recurring_count": len(recurring_txns),
            "total_monthly_recurring": total_monthly,
            "total_annual_recurring": total_annual,
            "analysis_months": months,
            "transactions": sorted(recurring_txns, key=lambda x: x["annual_cost"], reverse=True),
            "currency": "CAD"
        }

    def execute_function(self, function_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a function call from the LLM."""
        if function_name == "get_transactions":
            return self.get_transactions(**arguments)
        elif function_name == "get_spending_summary":
            return self.get_spending_summary(**arguments)
        elif function_name == "get_portfolio_summary":
            return self.get_portfolio_summary(**arguments)
        elif function_name == "budget_status":
            return self.budget_status(**arguments)
        elif function_name == "cashflow_summary":
            return self.cashflow_summary(**arguments)
        elif function_name == "recurring_analysis":
            return self.recurring_analysis(**arguments)
        elif function_name == "spending_patterns":
            return self.spending_patterns(**arguments)
        elif function_name == "merchant_insights":
            return self.merchant_insights(**arguments)
        elif function_name == "goal_progress":
            return self.goal_progress(**arguments)
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    def chat(self, query: str, conversation_history: Optional[list[dict]] = None) -> dict[str, Any]:
        """Process a chat query and return response."""
        start_time = time.time()
        
        # Build messages
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})
        
        functions_called = []
        max_iterations = 5  # Prevent infinite loops
        
        for _ in range(max_iterations):
            # Call LLM with function calling
            response = self.provider.chat(messages, self.FUNCTION_DEFINITIONS)
            
            # Check if LLM wants to call a function
            if response.get("message", {}).get("tool_calls"):
                for tool_call in response["message"]["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    # Execute function
                    result = self.execute_function(function_name, arguments)
                    functions_called.append({
                        "name": function_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                    # Add function result to messages
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result)
                    })
            else:
                # LLM is done, return final response
                execution_time_ms = int((time.time() - start_time) * 1000)
                return {
                    "response": response["message"]["content"],
                    "functions_called": functions_called,
                    "execution_time_ms": execution_time_ms
                }
        
        # Max iterations reached
        return {
            "response": "I'm having trouble processing your request. Please try rephrasing.",
            "functions_called": functions_called,
            "execution_time_ms": int((time.time() - start_time) * 1000)
        }
