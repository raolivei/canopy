"""Budget API endpoints for CRUD operations and tracking."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.db.session import DbSession
from backend.models.budget import (
    BudgetCategoryRequest,
    BudgetCategoryResponse,
    BudgetCategoryTracking,
    BudgetListResponse,
    BudgetMetadata,
    BudgetRequest,
    BudgetResponse,
    BudgetSummary,
    BudgetTrackingResponse,
    BudgetUpdateRequest,
)
from backend.services.budget_service import BudgetService

router = APIRouter(prefix="/v1/budgets", tags=["budgets"])


def _convert_budget_to_response(budget) -> BudgetResponse:
    """Convert database Budget model to BudgetResponse."""
    return BudgetResponse(
        id=budget.id,
        name=budget.name,
        currency=budget.currency,
        description=budget.description,
        is_active=budget.is_active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        categories=[
            BudgetCategoryResponse(
                id=cat.id,
                budget_id=cat.budget_id,
                category_name=cat.category_name,
                limit_amount=cat.limit_amount,
                period_type=cat.period_type,
                rollover_excess=cat.rollover_excess,
                created_at=cat.created_at,
                updated_at=cat.updated_at,
            )
            for cat in budget.categories
        ],
    )


@router.get("/", response_model=list[BudgetListResponse])
async def list_budgets(
    db: DbSession,
    active_only: bool = Query(False, description="Show only active budgets"),
):
    """List all budgets.

    Args:
        db: Database session
        active_only: If True, only return active budgets

    Returns:
        List of BudgetListResponse objects
    """
    service = BudgetService(db)
    budgets_data = service.get_all_budgets()
    return [BudgetListResponse(**b) for b in budgets_data]


@router.post("/", response_model=BudgetResponse, status_code=201)
async def create_budget(
    db: DbSession,
    budget_data: BudgetRequest,
):
    """Create a new budget.

    Args:
        db: Database session
        budget_data: Budget creation data (name, currency, description)

    Returns:
        Created BudgetResponse

    Raises:
        HTTPException: 400 if name is empty
    """
    service = BudgetService(db)
    try:
        budget = service.create_budget(
            name=budget_data.name,
            currency=budget_data.currency,
            description=budget_data.description,
        )
        return _convert_budget_to_response(budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    db: DbSession,
    budget_id: int,
):
    """Get budget details with all categories.

    Args:
        db: Database session
        budget_id: ID of the budget

    Returns:
        BudgetResponse with categories

    Raises:
        HTTPException: 404 if budget not found
    """
    service = BudgetService(db)
    budget = service.get_budget(budget_id)

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return _convert_budget_to_response(budget)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    db: DbSession,
    budget_id: int,
    budget_data: BudgetUpdateRequest,
):
    """Update budget metadata.

    Args:
        db: Database session
        budget_id: ID of the budget
        budget_data: Update data (name, description, is_active)

    Returns:
        Updated BudgetResponse

    Raises:
        HTTPException: 404 if budget not found
        HTTPException: 400 if invalid data
    """
    service = BudgetService(db)
    try:
        budget = service.update_budget(
            budget_id=budget_id,
            name=budget_data.name,
            description=budget_data.description,
            is_active=budget_data.is_active,
        )

        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")

        return _convert_budget_to_response(budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    db: DbSession,
    budget_id: int,
):
    """Delete a budget and all its categories.

    Args:
        db: Database session
        budget_id: ID of the budget

    Raises:
        HTTPException: 404 if budget not found
    """
    service = BudgetService(db)
    success = service.delete_budget(budget_id)

    if not success:
        raise HTTPException(status_code=404, detail="Budget not found")


@router.post("/{budget_id}/categories", response_model=BudgetCategoryResponse, status_code=201)
async def add_budget_category(
    db: DbSession,
    budget_id: int,
    category_data: BudgetCategoryRequest,
):
    """Add a category to a budget with a spending limit.

    Args:
        db: Database session
        budget_id: ID of the budget
        category_data: Category configuration (category_name, limit_amount, period_type, rollover_excess)

    Returns:
        Created BudgetCategoryResponse

    Raises:
        HTTPException: 404 if budget not found
        HTTPException: 400 if invalid input
    """
    service = BudgetService(db)
    try:
        budget_category = service.add_category_to_budget(
            budget_id=budget_id,
            category_name=category_data.category_name,
            limit_amount=category_data.limit_amount,
            period_type=category_data.period_type,
            rollover_excess=category_data.rollover_excess,
        )

        if not budget_category:
            raise HTTPException(status_code=404, detail="Budget not found")

        return BudgetCategoryResponse(
            id=budget_category.id,
            budget_id=budget_category.budget_id,
            category_name=budget_category.category_name,
            limit_amount=budget_category.limit_amount,
            period_type=budget_category.period_type,
            rollover_excess=budget_category.rollover_excess,
            created_at=budget_category.created_at,
            updated_at=budget_category.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{budget_id}/tracking", response_model=BudgetTrackingResponse)
async def get_budget_tracking(
    db: DbSession,
    budget_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get budget vs actuals tracking for a date range.

    Defaults to current month if dates not provided.

    Args:
        db: Database session
        budget_id: ID of the budget
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)

    Returns:
        BudgetTrackingResponse with period entries and summary

    Raises:
        HTTPException: 404 if budget not found
        HTTPException: 400 if invalid dates
    """
    service = BudgetService(db)

    try:
        # Default to current month if not provided
        if not start_date or not end_date:
            now = datetime.utcnow()
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get last day of current month
            import calendar

            days_in_month = calendar.monthrange(now.year, now.month)[1]
            end_dt = now.replace(day=days_in_month, hour=23, minute=59, second=59)
            start_date_str = start_dt.date().isoformat()
            end_date_str = end_dt.date().isoformat()
        else:
            # Parse ISO dates
            try:
                from datetime import date

                start_date_obj = date.fromisoformat(start_date)
                end_date_obj = date.fromisoformat(end_date)
                start_dt = datetime.combine(start_date_obj, datetime.min.time())
                end_dt = datetime.combine(end_date_obj, datetime.max.time())
                start_date_str = start_date
                end_date_str = end_date
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )

        # Get budget with tracking data
        data = service.get_budget_with_tracking(budget_id, start_dt, end_dt)

        # Convert category data to tracking format
        categories = [
            BudgetCategoryTracking(
                id=cat["id"],
                category_name=cat["category_name"],
                limit_amount=cat["limit_amount"],
                actual_spent=cat["actual_spent"],
                variance=cat["variance"],
                variance_pct=cat["variance_pct"],
                percent_used=cat["percent_used"],
                is_over_budget=cat["is_over_budget"],
            )
            for cat in data["categories"]
        ]

        summary = BudgetSummary(
            total_limit=data["summary"]["total_limit"],
            total_actual=data["summary"]["total_actual"],
            total_variance=data["summary"]["total_variance"],
            variance_pct=data["summary"]["variance_pct"],
            percent_used=data["summary"]["percent_used"],
            is_over_budget=data["summary"]["is_over_budget"],
        )

        return BudgetTrackingResponse(
            budget=BudgetMetadata(
                id=data["budget"]["id"],
                name=data["budget"]["name"],
                currency=data["budget"]["currency"],
                description=data["budget"]["description"],
                is_active=data["budget"]["is_active"],
            ),
            period_start=start_date_str,
            period_end=end_date_str,
            categories=categories,
            summary=summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve budget tracking: {str(e)}")
