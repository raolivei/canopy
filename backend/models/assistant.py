"""Pydantic models for AI Assistant API."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    query: str = Field(..., min_length=1, max_length=1000, description="User's question")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for follow-up questions")


class FunctionCall(BaseModel):
    """Function call made by the assistant."""

    name: str
    arguments: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    conversation_id: int
    message_id: int
    functions_called: list[FunctionCall]
    execution_time_ms: int


class Message(BaseModel):
    """A single message in conversation history."""

    id: int
    role: str  # 'user' or 'assistant'
    content: str
    functions_called: Optional[list[FunctionCall]] = None
    created_at: datetime


class Conversation(BaseModel):
    """Conversation with message history."""

    id: int
    created_at: datetime
    updated_at: datetime
    messages: list[Message]


# P3 Assistant Expansion Models


class BudgetStatusRequest(BaseModel):
    """Request for budget status."""

    month: Optional[str] = Field(None, description="Month in YYYY-MM format, defaults to current month")


class BudgetAlert(BaseModel):
    """Budget alert for a category."""

    category: str
    spent: float
    budget: float
    percent_used: float
    status: str  # "on_track", "warning", "critical"


class BudgetStatusResponse(BaseModel):
    """Response for budget status."""

    month: str
    total_spent: float
    total_budget: float
    percent_used: float
    alerts: list[BudgetAlert]
    on_track_categories: int
    warning_categories: int
    critical_categories: int


class CashflowSummaryRequest(BaseModel):
    """Request for cashflow summary."""

    month: Optional[str] = Field(None, description="Month in YYYY-MM format, defaults to current month")


class CashflowSummaryResponse(BaseModel):
    """Response for cashflow summary."""

    month: str
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    expense_breakdown: dict[str, float]


class RecurringAnalysisRequest(BaseModel):
    """Request for recurring transaction analysis."""

    months: int = Field(3, description="Number of months to analyze")


class RecurringTransaction(BaseModel):
    """A recurring transaction."""

    merchant: str
    category: str
    average_amount: float
    frequency: str  # "daily", "weekly", "monthly", "annual"
    next_date: Optional[str] = None
    annual_cost: float


class RecurringAnalysisResponse(BaseModel):
    """Response for recurring transaction analysis."""

    recurring_count: int
    total_monthly_recurring: float
    total_annual_recurring: float
    transactions: list[RecurringTransaction]


class SpendingPatternsRequest(BaseModel):
    """Request for spending patterns."""

    months: int = Field(3, description="Number of months to analyze")


class CategoryTrend(BaseModel):
    """Category spending trend."""

    category: str
    current_month: float
    previous_month: Optional[float]
    trend: str  # "up", "down", "stable"
    percent_change: Optional[float]


class SpendingAnomalyAlert(BaseModel):
    """Spending anomaly alert."""

    category: str
    amount: float
    vs_average: float
    percent_above_average: float
    flag: str  # "unusual_high", "unusual_low"


class SpendingPatternsResponse(BaseModel):
    """Response for spending patterns."""

    analysis_months: int
    top_categories: list[CategoryTrend]
    anomalies: list[SpendingAnomalyAlert]
    total_spending: float
    average_monthly: float


class MerchantInsightsRequest(BaseModel):
    """Request for merchant spending insights."""

    months: int = Field(3, description="Number of months to analyze")
    top_n: int = Field(10, description="Number of top merchants to return")


class MerchantSpending(BaseModel):
    """Merchant spending details."""

    merchant: str
    category: str
    total_spent: float
    transaction_count: int
    average_transaction: float
    frequency: str  # "daily", "weekly", "monthly"


class MerchantInsightsResponse(BaseModel):
    """Response for merchant insights."""

    analysis_months: int
    top_merchants: list[MerchantSpending]
    total_unique_merchants: int
    total_merchant_spending: float


class GoalProgressRequest(BaseModel):
    """Request for goal progress."""
    pass


class SavingsGoal(BaseModel):
    """Savings goal progress."""

    name: str
    target_amount: float
    current_amount: float
    percent_complete: float
    monthly_contribution: float
    months_to_goal: Optional[float]
    status: str  # "on_track", "behind", "completed"


class NetWorthTarget(BaseModel):
    """Net worth target progress."""

    target: float
    current: float
    percent_complete: float
    monthly_growth: float
    months_to_target: Optional[float]


class FireTimeline(BaseModel):
    """FIRE (Financial Independence, Retire Early) timeline."""

    fire_number: float  # 25x annual expenses
    current_portfolio: float
    monthly_savings: float
    assumed_annual_return: float
    years_to_fire: Optional[float]


class GoalProgressResponse(BaseModel):
    """Response for goal progress."""

    savings_goals: list[SavingsGoal]
    net_worth: NetWorthTarget
    fire_timeline: Optional[FireTimeline]
    overall_progress: str  # "ahead", "on_track", "behind"
