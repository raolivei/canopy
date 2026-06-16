"""Pydantic models for Recurring Transaction Detection API.

Canopy - Personal Finance Platform
"""

from datetime import date

from pydantic import BaseModel, Field


class RecurringPattern(BaseModel):
    """A detected recurring transaction pattern."""

    merchant: str = Field(..., description="Merchant name")
    category: str = Field(..., description="Transaction category")
    avg_amount: float = Field(..., description="Average transaction amount")
    frequency_days: int = Field(
        ..., description="Average days between transactions (7, 14, 30, etc.)"
    )
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0.0, le=1.0)
    last_occurrence: date = Field(..., description="Date of last transaction")
    predicted_next: date = Field(..., description="Predicted date of next transaction")
    occurrences: int = Field(..., description="Number of occurrences detected", ge=3)


class RecurringPrediction(BaseModel):
    """Prediction for an upcoming recurring transaction."""

    pattern: RecurringPattern = Field(..., description="The recurring pattern")
    days_until_next: int = Field(
        ..., description="Days until predicted next transaction"
    )
    amount_range: tuple[float, float] = Field(
        ..., description="Expected amount range (min, max) based on ±10% variance"
    )


class RecurringDetectionRequest(BaseModel):
    """Request for detecting recurring patterns."""

    months: int = Field(3, description="Number of months to analyze", ge=1, le=24)


class RecurringDetectionResponse(BaseModel):
    """Response for recurring pattern detection."""

    patterns: list[RecurringPattern]
    total_patterns: int = Field(..., description="Number of patterns detected")
    months_analyzed: int = Field(..., description="Number of months analyzed")


class RecurringPredictionsRequest(BaseModel):
    """Request for recurring transaction predictions."""

    next_days: int = Field(
        30, description="Number of days ahead to predict", ge=1, le=90
    )


class RecurringPredictionsResponse(BaseModel):
    """Response for recurring transaction predictions."""

    predictions: list[RecurringPrediction]
    total_predictions: int = Field(..., description="Number of predictions")
    prediction_window_days: int = Field(..., description="Prediction window in days")


class TransactionClassificationRequest(BaseModel):
    """Request to classify a transaction as recurring or not."""

    transaction_id: int = Field(..., description="Transaction ID to classify")


class TransactionClassificationResponse(BaseModel):
    """Response for transaction classification."""

    is_recurring: bool = Field(..., description="Whether transaction is recurring")
    confidence: float | None = Field(
        None, description="Confidence score (0-1) if recurring"
    )
    pattern: RecurringPattern | None = Field(
        None, description="Matched pattern if recurring"
    )
