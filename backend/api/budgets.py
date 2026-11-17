"""Budget API: CRUD, category limits and period status."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status

from backend.db.session import DbSession
from backend.models.budget import (
    Budget,
    BudgetCategory,
    BudgetCategoryCreate,
    BudgetCategoryUpdate,
    BudgetCreate,
    BudgetStatus,
    BudgetUpdate,
)
from backend.services.budget_service import BudgetNotFound, BudgetService, CategoryNotFound, DuplicateCategory
from backend.services.calculation import parse_month

router = APIRouter(prefix="/v1/budgets", tags=["budgets"])


def _not_found(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _conflict(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/", response_model=Budget, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, db: DbSession) -> Budget:
    """Create a budget with optional category limits."""
    try:
        return Budget.model_validate(BudgetService(db).create_budget(data))
    except DuplicateCategory as exc:
        raise _conflict(exc) from exc


@router.get("/", response_model=list[Budget])
def list_budgets(
    db: DbSession,
    active_only: bool = Query(True, description="Hide soft-deleted budgets"),
) -> list[Budget]:
    """List budgets with their categories (one query per table, no N+1)."""
    return [Budget.model_validate(b) for b in BudgetService(db).list_budgets(active_only=active_only)]


@router.get("/{budget_id}", response_model=Budget)
def get_budget(budget_id: int, db: DbSession) -> Budget:
    try:
        return Budget.model_validate(BudgetService(db).get_budget(budget_id))
    except BudgetNotFound as exc:
        raise _not_found(exc) from exc


@router.put("/{budget_id}", response_model=Budget)
def update_budget(budget_id: int, data: BudgetUpdate, db: DbSession) -> Budget:
    try:
        return Budget.model_validate(BudgetService(db).update_budget(budget_id, data))
    except BudgetNotFound as exc:
        raise _not_found(exc) from exc


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, db: DbSession) -> Response:
    """Soft-delete a budget (it leaves active lists; history is kept)."""
    try:
        BudgetService(db).delete_budget(budget_id)
    except BudgetNotFound as exc:
        raise _not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{budget_id}/categories", response_model=BudgetCategory, status_code=status.HTTP_201_CREATED)
def add_category(budget_id: int, data: BudgetCategoryCreate, db: DbSession) -> BudgetCategory:
    try:
        return BudgetCategory.model_validate(BudgetService(db).add_category(budget_id, data))
    except BudgetNotFound as exc:
        raise _not_found(exc) from exc
    except DuplicateCategory as exc:
        raise _conflict(exc) from exc


@router.put("/{budget_id}/categories/{category_id}", response_model=BudgetCategory)
def update_category(budget_id: int, category_id: int, data: BudgetCategoryUpdate, db: DbSession) -> BudgetCategory:
    try:
        return BudgetCategory.model_validate(BudgetService(db).update_category(budget_id, category_id, data))
    except (BudgetNotFound, CategoryNotFound) as exc:
        raise _not_found(exc) from exc
    except DuplicateCategory as exc:
        raise _conflict(exc) from exc


@router.delete("/{budget_id}/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(budget_id: int, category_id: int, db: DbSession) -> Response:
    try:
        BudgetService(db).delete_category(budget_id, category_id)
    except (BudgetNotFound, CategoryNotFound) as exc:
        raise _not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{budget_id}/status", response_model=BudgetStatus)
def get_budget_status(
    budget_id: int,
    db: DbSession,
    month: str | None = Query(None, description="YYYY-MM inside the period to report (defaults to today's month)"),
) -> BudgetStatus:
    """Spend against the budget and each category limit for one period."""
    if month is not None:
        try:
            parse_month(month)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    try:
        return BudgetStatus(**BudgetService(db).get_budget_status(budget_id, month))
    except BudgetNotFound as exc:
        raise _not_found(exc) from exc
