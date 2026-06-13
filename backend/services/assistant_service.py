"""AI Assistant service with OpenClaw/Ollama integration for natural language queries."""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from ollama import Client as OllamaClient
from openai import OpenAI
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from backend.db.models.transaction import Transaction as TransactionModel
from backend.db.models.asset import Asset as AssetModel
from backend.db.models.budget import Budget as BudgetModel, BudgetCategory, BudgetTracking
from backend.services.portfolio_calculator import PortfolioCalculator
from backend.services.recurring_service import RecurringService


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
                "name": "get_accounts",
                "description": "Get all financial accounts (checking, savings, credit cards, investments, loans). Returns account types, balances, and currency.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_budget_status",
                "description": "Get current month budget status including limits, actual spending, and variance by category",
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
                "name": "get_recurring_summary",
                "description": "Get list of detected recurring transactions (subscriptions, salary, etc.) with frequency and next expected date",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lookback_months": {
                            "type": "integer",
                            "description": "Number of months to analyze for patterns (default: 12)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_cashflow_analysis",
                "description": "Get monthly income, expenses, and savings trend for the last 12 months",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "months": {
                            "type": "integer",
                            "description": "Number of months to analyze (default: 12)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_spending_patterns",
                "description": "Analyze spending patterns including top merchants, top categories, and spending trends",
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
                "name": "get_merchant_insights",
                "description": "Get detailed spending history with a specific merchant including total spent, frequency, and average amount",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "merchant_name": {
                            "type": "string",
                            "description": "Name of merchant to analyze"
                        },
                        "months": {
                            "type": "integer",
                            "description": "Number of months to look back (default: 12)"
                        }
                    },
                    "required": ["merchant_name"]
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
        self.recurring_service = RecurringService(db)

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

    def get_accounts(self) -> list[dict[str, Any]]:
        """Get all financial accounts with balances and types."""
        assets = self.db.execute(select(AssetModel)).scalars().all()

        accounts = []
        for asset in assets:
            # Get current balance
            balance_map = self.portfolio_calc.native_balances_from_history([asset.id])
            balance = balance_map.get(asset.id, Decimal(0))

            accounts.append({
                "name": asset.name,
                "symbol": asset.symbol,
                "type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else str(asset.asset_type),
                "balance": float(balance),
                "currency": asset.currency,
                "institution": asset.institution,
                "last_updated": asset.price_updated_at.isoformat() if asset.price_updated_at else None
            })

        return accounts

    def get_budget_status(self, month: Optional[str] = None) -> dict[str, Any]:
        """Get budget status for a given month."""
        if not month:
            today = datetime.utcnow()
            month = today.strftime("%Y-%m")

        # Parse month
        try:
            year, month_num = map(int, month.split("-"))
            period_start = datetime(year, month_num, 1)
            if month_num == 12:
                period_end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = datetime(year, month_num + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            return {"error": "Invalid month format. Use YYYY-MM."}

        # Get active budgets
        budgets = self.db.execute(
            select(BudgetModel).where(BudgetModel.is_active == True)
        ).scalars().all()

        if not budgets:
            return {
                "month": month,
                "budget_limit": 0,
                "actual_spent": 0,
                "variance": 0,
                "categories": [],
                "message": "No active budgets found"
            }

        # Get all transactions for the month
        transactions = self.db.execute(
            select(TransactionModel).where(
                TransactionModel.date >= period_start,
                TransactionModel.date <= period_end,
                TransactionModel.type == "expense"
            )
        ).scalars().all()

        # Calculate totals by category
        category_totals: dict[str, float] = {}
        for tx in transactions:
            category = tx.category or "Uncategorized"
            category_totals[category] = category_totals.get(category, 0) + float(abs(tx.amount))

        # Build budget status
        total_budget_limit = Decimal(0)
        total_actual_spent = Decimal(0)
        categories = []

        for budget in budgets:
            for budget_cat in budget.categories:
                total_budget_limit += budget_cat.limit_amount
                actual = Decimal(str(category_totals.get(budget_cat.category_name, 0)))
                total_actual_spent += actual

                variance = float(budget_cat.limit_amount - actual)
                categories.append({
                    "name": budget_cat.category_name,
                    "limit": float(budget_cat.limit_amount),
                    "actual": float(actual),
                    "variance": variance,
                    "status": "over" if actual > budget_cat.limit_amount else "under"
                })

        return {
            "month": month,
            "budget_limit": float(total_budget_limit),
            "actual_spent": float(total_actual_spent),
            "variance": float(total_budget_limit - total_actual_spent),
            "categories": categories,
            "currency": "CAD"
        }

    def get_recurring_summary(self, lookback_months: int = 12) -> list[dict[str, Any]]:
        """Get detected recurring transactions."""
        patterns = self.recurring_service.detect_recurring_transactions(lookback_months)

        return [
            {
                "merchant": pattern.merchant,
                "category": pattern.category,
                "average_amount": float(pattern.average_amount),
                "frequency": pattern.frequency.value,
                "next_expected": pattern.next_expected.isoformat() if pattern.next_expected else None,
                "confidence": pattern.confidence,
                "occurrences": len(pattern.occurrences),
                "currency": "CAD"
            }
            for pattern in patterns
        ]

    def get_cashflow_analysis(self, months: int = 12) -> dict[str, Any]:
        """Get monthly cashflow analysis."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=months * 30)

        # Group transactions by month
        monthly_data: dict[str, dict[str, float]] = {}

        transactions = self.db.execute(
            select(TransactionModel).where(TransactionModel.date >= start_date)
        ).scalars().all()

        for tx in transactions:
            month_key = tx.date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "income": 0,
                    "expenses": 0,
                    "transfers": 0
                }

            if tx.type == "income":
                monthly_data[month_key]["income"] += float(tx.amount)
            elif tx.type == "expense":
                monthly_data[month_key]["expenses"] += float(abs(tx.amount))
            elif tx.type == "transfer":
                monthly_data[month_key]["transfers"] += float(abs(tx.amount))

        # Calculate savings
        monthly_list = []
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            savings = data["income"] - data["expenses"]
            savings_rate = (savings / data["income"] * 100) if data["income"] > 0 else 0

            monthly_list.append({
                "month": month,
                "income": data["income"],
                "expenses": data["expenses"],
                "savings": savings,
                "savings_rate": round(savings_rate, 2),
                "transfers": data["transfers"]
            })

        # Determine trend
        trend = "stable"
        if len(monthly_list) >= 2:
            recent_avg = sum(m["savings"] for m in monthly_list[-3:]) / 3
            previous_avg = sum(m["savings"] for m in monthly_list[-6:-3]) / 3 if len(monthly_list) >= 6 else recent_avg

            if recent_avg > previous_avg * 1.1:
                trend = "up"
            elif recent_avg < previous_avg * 0.9:
                trend = "down"

        return {
            "monthly_data": monthly_list,
            "trend": trend,
            "average_monthly_income": sum(m["income"] for m in monthly_list) / len(monthly_list) if monthly_list else 0,
            "average_monthly_expenses": sum(m["expenses"] for m in monthly_list) / len(monthly_list) if monthly_list else 0,
            "average_monthly_savings": sum(m["savings"] for m in monthly_list) / len(monthly_list) if monthly_list else 0,
            "currency": "CAD"
        }

    def analyze_spending_patterns(self, months: int = 3) -> dict[str, Any]:
        """Analyze spending patterns."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=months * 30)

        transactions = self.db.execute(
            select(TransactionModel).where(
                TransactionModel.date >= start_date,
                TransactionModel.type == "expense"
            )
        ).scalars().all()

        # Top merchants
        merchant_totals: dict[str, float] = {}
        for tx in transactions:
            merchant = tx.merchant or tx.description or "Unknown"
            merchant_totals[merchant] = merchant_totals.get(merchant, 0) + float(abs(tx.amount))

        top_merchants = sorted(
            [{"name": m, "total": t, "count": sum(1 for tx in transactions if (tx.merchant or tx.description) == m)}
             for m, t in merchant_totals.items()],
            key=lambda x: x["total"],
            reverse=True
        )[:5]

        # Top categories
        category_totals: dict[str, float] = {}
        for tx in transactions:
            category = tx.category or "Uncategorized"
            category_totals[category] = category_totals.get(category, 0) + float(abs(tx.amount))

        top_categories = sorted(
            [{"name": c, "total": t} for c, t in category_totals.items()],
            key=lambda x: x["total"],
            reverse=True
        )[:5]

        # Trends
        trends = []
        week_ago = now - timedelta(days=7)
        week_before = week_ago - timedelta(days=7)

        week_spending = sum(float(abs(tx.amount)) for tx in transactions if tx.date >= week_ago)
        previous_week_spending = sum(float(abs(tx.amount)) for tx in transactions if week_before <= tx.date < week_ago)

        if previous_week_spending > 0:
            trend = ((week_spending - previous_week_spending) / previous_week_spending) * 100
            trends.append({
                "period": "week",
                "change_percent": round(trend, 2),
                "direction": "up" if trend > 0 else "down" if trend < 0 else "stable"
            })

        total_spending = sum(float(abs(tx.amount)) for tx in transactions)

        return {
            "period_months": months,
            "total_spending": total_spending,
            "transaction_count": len(transactions),
            "top_merchants": top_merchants,
            "top_categories": top_categories,
            "trends": trends,
            "currency": "CAD"
        }

    def get_merchant_insights(self, merchant_name: str, months: int = 12) -> dict[str, Any]:
        """Get spending insights for a specific merchant."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=months * 30)

        transactions = self.db.execute(
            select(TransactionModel).where(
                TransactionModel.date >= start_date,
                or_(
                    TransactionModel.merchant.ilike(f"%{merchant_name}%"),
                    TransactionModel.description.ilike(f"%{merchant_name}%")
                )
            )
        ).scalars().all()

        if not transactions:
            return {
                "merchant": merchant_name,
                "total_spent": 0,
                "transaction_count": 0,
                "message": f"No transactions found for {merchant_name}"
            }

        amounts = [float(abs(tx.amount)) for tx in transactions]
        total_spent = sum(amounts)

        return {
            "merchant": merchant_name,
            "total_spent": total_spent,
            "transaction_count": len(transactions),
            "average_amount": round(total_spent / len(transactions), 2),
            "max_amount": max(amounts),
            "min_amount": min(amounts),
            "first_transaction": min(transactions, key=lambda x: x.date).date.isoformat(),
            "last_transaction": max(transactions, key=lambda x: x.date).date.isoformat(),
            "frequency_per_month": round(len(transactions) / max(1, months), 2),
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
        elif function_name == "get_accounts":
            return self.get_accounts(**arguments)
        elif function_name == "get_budget_status":
            return self.get_budget_status(**arguments)
        elif function_name == "get_recurring_summary":
            return self.get_recurring_summary(**arguments)
        elif function_name == "get_cashflow_analysis":
            return self.get_cashflow_analysis(**arguments)
        elif function_name == "analyze_spending_patterns":
            return self.analyze_spending_patterns(**arguments)
        elif function_name == "get_merchant_insights":
            return self.get_merchant_insights(**arguments)
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
