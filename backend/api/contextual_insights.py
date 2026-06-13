"""Contextual insights API for alerts, anomalies, and predictions."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.contextual_insights import (
    ContextualInsightsService,
    BudgetInsight,
    MoMComparison,
    TransactionAnomaly,
    RecurringPrediction,
)

router = APIRouter(prefix="/v1/contextual-insights", tags=["contextual-insights"])


class BudgetInsightResponse(BaseModel):
    """Budget warning response."""

    category_name: str
    type: str
    actual_spent: float
    budget_limit: float
    percent_used: float
    message: str


class MoMComparisonResponse(BaseModel):
    """Month-over-month comparison response."""

    category_name: str
    current_month_amount: float
    previous_month_amount: float
    change_percent: float
    type: str
    message: str


class TransactionAnomalyResponse(BaseModel):
    """Transaction anomaly response."""

    transaction_id: str
    merchant: str
    amount: float
    category: str
    deviation_percent: float
    type: str
    message: str


class RecurringPredictionResponse(BaseModel):
    """Recurring transaction prediction response."""

    merchant: str
    category: str
    expected_amount: float
    expected_date: str
    confidence: float
    message: str


class ContextualInsightsSummaryResponse(BaseModel):
    """Complete contextual insights summary."""

    budget_warnings: list[BudgetInsightResponse]
    mom_comparisons: list[MoMComparisonResponse]
    anomalies: list[TransactionAnomalyResponse]
    recurring_predictions: list[RecurringPredictionResponse]


@router.get("/budget-warnings", response_model=list[BudgetInsightResponse])
def get_budget_warnings(db: Session = Depends(get_db)):
    """Get budget warning insights for current month."""
    service = ContextualInsightsService(db)
    insights = service.get_budget_warnings()
    return [
        BudgetInsightResponse(
            category_name=i.category_name,
            type=i.type,
            actual_spent=float(i.actual_spent),
            budget_limit=float(i.budget_limit),
            percent_used=i.percent_used,
            message=i.message,
        )
        for i in insights
    ]


@router.get("/mom-comparisons", response_model=list[MoMComparisonResponse])
def get_mom_comparisons(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """Get month-over-month spending comparisons."""
    service = ContextualInsightsService(db)
    comparisons = service.get_mom_comparisons(limit=limit)
    return [
        MoMComparisonResponse(
            category_name=c.category_name,
            current_month_amount=float(c.current_month_amount),
            previous_month_amount=float(c.previous_month_amount),
            change_percent=c.change_percent,
            type=c.type,
            message=c.message,
        )
        for c in comparisons
    ]


@router.get("/anomalies", response_model=list[TransactionAnomalyResponse])
def get_anomalies(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """Detect unusual transactions."""
    service = ContextualInsightsService(db)
    anomalies = service.detect_anomalies(limit=limit)
    return [
        TransactionAnomalyResponse(
            transaction_id=a.transaction_id,
            merchant=a.merchant,
            amount=float(a.amount),
            category=a.category,
            deviation_percent=a.deviation_percent,
            type=a.type,
            message=a.message,
        )
        for a in anomalies
    ]


@router.get("/recurring-predictions", response_model=list[RecurringPredictionResponse])
def get_recurring_predictions(
    limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)
):
    """Predict upcoming recurring transactions."""
    service = ContextualInsightsService(db)
    predictions = service.predict_recurring(limit=limit)
    return [
        RecurringPredictionResponse(
            merchant=p.merchant,
            category=p.category,
            expected_amount=float(p.expected_amount),
            expected_date=p.expected_date.isoformat(),
            confidence=p.confidence,
            message=p.message,
        )
        for p in predictions
    ]


@router.get("/summary", response_model=ContextualInsightsSummaryResponse)
def get_insights_summary(db: Session = Depends(get_db)):
    """Get complete contextual insights summary."""
    service = ContextualInsightsService(db)

    budget_warnings = service.get_budget_warnings()
    mom_comparisons = service.get_mom_comparisons()
    anomalies = service.detect_anomalies()
    recurring_predictions = service.predict_recurring()

    return ContextualInsightsSummaryResponse(
        budget_warnings=[
            BudgetInsightResponse(
                category_name=i.category_name,
                type=i.type,
                actual_spent=float(i.actual_spent),
                budget_limit=float(i.budget_limit),
                percent_used=i.percent_used,
                message=i.message,
            )
            for i in budget_warnings
        ],
        mom_comparisons=[
            MoMComparisonResponse(
                category_name=c.category_name,
                current_month_amount=float(c.current_month_amount),
                previous_month_amount=float(c.previous_month_amount),
                change_percent=c.change_percent,
                type=c.type,
                message=c.message,
            )
            for c in mom_comparisons
        ],
        anomalies=[
            TransactionAnomalyResponse(
                transaction_id=a.transaction_id,
                merchant=a.merchant,
                amount=float(a.amount),
                category=a.category,
                deviation_percent=a.deviation_percent,
                type=a.type,
                message=a.message,
            )
            for a in anomalies
        ],
        recurring_predictions=[
            RecurringPredictionResponse(
                merchant=p.merchant,
                category=p.category,
                expected_amount=float(p.expected_amount),
                expected_date=p.expected_date.isoformat(),
                confidence=p.confidence,
                message=p.message,
            )
            for p in recurring_predictions
        ],
    )
