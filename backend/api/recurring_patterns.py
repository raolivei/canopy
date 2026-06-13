"""Recurring patterns API endpoints for managing recurring transaction patterns."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.db.models.recurring_pattern import RecurringPattern as RecurringPatternModel
from backend.db.models.recurring_pattern import RecurringFrequency
from backend.db.session import DbSession
from backend.services.recurring_service import RecurringService

router = APIRouter(prefix="/v1/recurring", tags=["recurring"])


class RecurringPatternResponse(BaseModel):
    """Response model for recurring pattern."""

    id: Optional[int] = None
    merchant: str
    category: Optional[str] = None
    average_amount: float
    amount_variance: float
    frequency: str
    next_expected: Optional[str] = None
    confidence: int
    occurrences: list[str] = []
    should_skip_dates: list[str] = []
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class RecurringPatternUpdate(BaseModel):
    """Model for updating a recurring pattern."""

    frequency: Optional[str] = None
    average_amount: Optional[float] = None
    next_expected: Optional[str] = None
    is_active: Optional[bool] = None


class RecurringDetectionResponse(BaseModel):
    """Response model for detected recurring patterns."""

    detected: list[RecurringPatternResponse]
    total_count: int


def _db_to_response(pattern: RecurringPatternModel) -> RecurringPatternResponse:
    """Convert database model to response model."""
    return RecurringPatternResponse(
        id=pattern.id,
        merchant=pattern.merchant,
        category=pattern.category,
        average_amount=float(pattern.average_amount),
        amount_variance=float(pattern.amount_variance),
        frequency=pattern.frequency,
        next_expected=pattern.next_expected.isoformat() if pattern.next_expected else None,
        confidence=pattern.confidence,
        occurrences=pattern.occurrences or [],
        should_skip_dates=pattern.should_skip_dates or [],
        is_active=pattern.is_active,
        created_at=pattern.created_at.isoformat() if pattern.created_at else None,
        updated_at=pattern.updated_at.isoformat() if pattern.updated_at else None,
    )


@router.get("/detect", response_model=RecurringDetectionResponse)
async def detect_recurring_patterns(
    db: DbSession,
    lookback_months: int = Query(12, ge=1, le=60, description="Months to analyze"),
):
    """Detect recurring transaction patterns.

    Analyzes transaction history to identify patterns like subscriptions and salary.
    Returns patterns with confidence >= 70%.
    """
    try:
        service = RecurringService(db)
        detected = service.detect_recurring_transactions(lookback_months=lookback_months)

        return RecurringDetectionResponse(
            detected=[
                RecurringPatternResponse(
                    merchant=p.merchant,
                    category=p.category,
                    average_amount=float(p.average_amount),
                    amount_variance=float(p.amount_variance),
                    frequency=p.frequency.value,
                    next_expected=p.next_expected.isoformat() if p.next_expected else None,
                    confidence=p.confidence,
                    occurrences=[d.isoformat() for d in p.occurrences],
                    should_skip_dates=[d.isoformat() for d in p.should_skip_dates],
                )
                for p in detected
            ],
            total_count=len(detected),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/", response_model=list[RecurringPatternResponse])
async def get_recurring_patterns(
    db: DbSession,
    active_only: bool = Query(True, description="Only return active patterns"),
):
    """Get all stored recurring patterns."""
    try:
        query = db.query(RecurringPatternModel)
        if active_only:
            query = query.filter(RecurringPatternModel.is_active is True)
        patterns = query.order_by(RecurringPatternModel.next_expected).all()
        return [_db_to_response(p) for p in patterns]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch patterns: {str(e)}")


@router.post("/", response_model=RecurringPatternResponse)
async def create_recurring_pattern(
    db: DbSession,
    pattern: RecurringPatternResponse,
):
    """Create/approve a new recurring pattern."""
    try:
        db_pattern = RecurringPatternModel(
            merchant=pattern.merchant,
            category=pattern.category,
            average_amount=Decimal(str(pattern.average_amount)),
            amount_variance=Decimal(str(pattern.amount_variance)),
            frequency=pattern.frequency,
            next_expected=datetime.fromisoformat(pattern.next_expected) if pattern.next_expected else None,
            confidence=pattern.confidence,
            occurrences=pattern.occurrences,
            should_skip_dates=pattern.should_skip_dates,
            is_active=True,
        )
        db.add(db_pattern)
        db.commit()
        db.refresh(db_pattern)
        return _db_to_response(db_pattern)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create pattern: {str(e)}")


@router.put("/{pattern_id}", response_model=RecurringPatternResponse)
async def update_recurring_pattern(
    db: DbSession,
    pattern_id: int,
    update: RecurringPatternUpdate,
):
    """Update an existing recurring pattern."""
    try:
        db_pattern = db.query(RecurringPatternModel).filter(RecurringPatternModel.id == pattern_id).first()
        if not db_pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")

        if update.frequency is not None:
            db_pattern.frequency = update.frequency
        if update.average_amount is not None:
            db_pattern.average_amount = Decimal(str(update.average_amount))
        if update.next_expected is not None:
            db_pattern.next_expected = datetime.fromisoformat(update.next_expected)
        if update.is_active is not None:
            db_pattern.is_active = update.is_active

        db.commit()
        db.refresh(db_pattern)
        return _db_to_response(db_pattern)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update pattern: {str(e)}")


@router.delete("/{pattern_id}")
async def delete_recurring_pattern(
    db: DbSession,
    pattern_id: int,
):
    """Delete a recurring pattern."""
    try:
        db_pattern = db.query(RecurringPatternModel).filter(RecurringPatternModel.id == pattern_id).first()
        if not db_pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")

        db.delete(db_pattern)
        db.commit()
        return {"status": "deleted", "id": pattern_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete pattern: {str(e)}")
