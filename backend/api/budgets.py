"""Budget API endpoints for managing spending budgets and limits.

Canopy - Personal Finance Platform
"""

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.db.models.budget import Budget as BudgetModel
from backend.db.models.budget import BudgetCategory as BudgetCategoryModel
from backend.db.session import DbSession
from backend.models.budget import (
    Budget,
    BudgetCategory,
    BudgetCategoryCreate,
    BudgetCreate,
    BudgetStatus,
    BudgetUpdate,
)
from backend.services.budget_service import BudgetService

router = APIRouter(prefix="/v1/budgets", tags=["budgets"])


def _db_to_response(budget: BudgetModel) -> Budget:
    """Convert database model to response model."""
    return Budget(
        id=budget.id,
        name=budget.name,
        amount=float(budget.amount),
        period=budget.period,
        user_id=budget.user_id,
        active=budget.active,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
        categories=[
            BudgetCategory(
                id=cat.id,
                budget_id=cat.budget_id,
                category_name=cat.category_name,
                amount_limit=float(cat.amount_limit),
                created_at=cat.created_at,
                updated_at=cat.updated_at,
            )
            for cat in budget.categories
        ],
    )


@router.post("/", response_model=Budget, status_code=201)
async def create_budget(budget_data: BudgetCreate, db: DbSession):
    """Create a new budget with optional category breakdowns."""
    new_budget = BudgetModel(
        name=budget_data.name,
        amount=Decimal(str(budget_data.amount)),
        period=budget_data.period,
        user_id=budget_data.user_id,
        active=True,
    )

    db.add(new_budget)
    db.flush()

    # Add categories if provided
    for cat_data in budget_data.categories:
        category = BudgetCategoryModel(
            budget_id=new_budget.id,
            category_name=cat_data.category_name,
            amount_limit=Decimal(str(cat_data.amount_limit)),
        )
        db.add(category)

    db.commit()
    db.refresh(new_budget)

    return _db_to_response(new_budget)


@router.get("/", response_model=list[Budget])
async def list_budgets(db: DbSession):
    """List all budgets with their categories."""
    budgets = db.execute(
        select(BudgetModel).where(BudgetModel.active == True)  # noqa: E712
    ).scalars().all()
    return [_db_to_response(b) for b in budgets]


@router.get("/{budget_id}", response_model=Budget)
async def get_budget(budget_id: int, db: DbSession):
    """Get budget details by ID."""
    budget = db.execute(
        select(BudgetModel).where(BudgetModel.id == budget_id)
    ).scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return _db_to_response(budget)


@router.patch("/{budget_id}", response_model=Budget)
async def update_budget(budget_id: int, update_data: BudgetUpdate, db: DbSession):
    """Update an existing budget."""
    budget = db.execute(
        select(BudgetModel).where(BudgetModel.id == budget_id)
    ).scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if update_data.name is not None:
        budget.name = update_data.name
    if update_data.amount is not None:
        budget.amount = Decimal(str(update_data.amount))
    if update_data.period is not None:
        budget.period = update_data.period
    if update_data.active is not None:
        budget.active = update_data.active

    db.commit()
    db.refresh(budget)

    return _db_to_response(budget)


@router.delete("/{budget_id}")
async def delete_budget(budget_id: int, db: DbSession):
    """Delete a budget (soft delete)."""
    budget = db.execute(
        select(BudgetModel).where(BudgetModel.id == budget_id)
    ).scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    budget.active = False
    db.commit()

    return {"message": f"Budget {budget_id} deleted"}


@router.post("/{budget_id}/categories", response_model=BudgetCategory, status_code=201)
async def add_category(budget_id: int, category_data: BudgetCategoryCreate, db: DbSession):
    """Add a category to a budget."""
    budget = db.execute(
        select(BudgetModel).where(BudgetModel.id == budget_id)
    ).scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    existing = db.execute(
        select(BudgetCategoryModel).where(
            BudgetCategoryModel.budget_id == budget_id,
            BudgetCategoryModel.category_name == category_data.category_name,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{category_data.category_name}' already exists",
        )

    category = BudgetCategoryModel(
        budget_id=budget_id,
        category_name=category_data.category_name,
        amount_limit=Decimal(str(category_data.amount_limit)),
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return BudgetCategory(
        id=category.id,
        budget_id=category.budget_id,
        category_name=category.category_name,
        amount_limit=float(category.amount_limit),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.patch("/{budget_id}/categories/{category_id}", response_model=BudgetCategory)
async def update_category(
    budget_id: int,
    category_id: int,
    update_data: BudgetCategoryCreate,
    db: DbSession,
):
    """Update a budget category."""
    category = db.execute(
        select(BudgetCategoryModel).where(
            BudgetCategoryModel.id == category_id,
            BudgetCategoryModel.budget_id == budget_id,
        )
    ).scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.category_name = update_data.category_name
    category.amount_limit = Decimal(str(update_data.amount_limit))

    db.commit()
    db.refresh(category)

    return BudgetCategory(
        id=category.id,
        budget_id=category.budget_id,
        category_name=category.category_name,
        amount_limit=float(category.amount_limit),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.delete("/{budget_id}/categories/{category_id}")
async def delete_category(budget_id: int, category_id: int, db: DbSession):
    """Remove a category from a budget."""
    category = db.execute(
        select(BudgetCategoryModel).where(
            BudgetCategoryModel.id == category_id,
            BudgetCategoryModel.budget_id == budget_id,
        )
    ).scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    return {"message": f"Category {category_id} deleted"}


@router.get("/{budget_id}/status", response_model=BudgetStatus)
async def get_budget_status(budget_id: int, db: DbSession):
    """Get budget status for the current period."""
    service = BudgetService(db)

    try:
        status = service.get_budget_status(budget_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{budget_id}/overspending")
async def get_overspending_categories(budget_id: int, db: DbSession):
    """Get categories that are over budget."""
    service = BudgetService(db)

    try:
        overspending = service.get_overspending_categories(budget_id)
        return {"overspending": overspending}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{budget_id}/projection")
async def get_month_end_projection(budget_id: int, db: DbSession):
    """Project month-end spending based on trends."""
    service = BudgetService(db)

    try:
        projection = service.get_month_end_projection(budget_id)
        return projection
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
