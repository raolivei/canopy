"""AI Assistant service with OpenClaw/Ollama integration for natural language queries."""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

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
    
    def execute_function(self, function_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a function call from the LLM."""
        if function_name == "get_transactions":
            return self.get_transactions(**arguments)
        elif function_name == "get_spending_summary":
            return self.get_spending_summary(**arguments)
        elif function_name == "get_portfolio_summary":
            return self.get_portfolio_summary(**arguments)
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
