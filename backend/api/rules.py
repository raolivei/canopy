"""API endpoints for transaction rules engine."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.models.rule import Rule as RuleModel
from backend.services.rule_service import RuleService
from backend.models.rule import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleListResponse,
)

router = APIRouter(prefix="/v1/rules", tags=["rules"])


@router.get("/", response_model=RuleListResponse)
def list_rules(
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> RuleListResponse:
    """List all transaction rules.

    Args:
        active_only: Filter to active rules only
        db: Database session

    Returns:
        List of rules
    """
    service = RuleService(db)
    rules = service.list_rules(active_only=active_only)
    return RuleListResponse(
        total=len(rules),
        rules=[RuleResponse.from_model(r) for r in rules],
    )


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    rule_data: RuleCreate,
    db: Session = Depends(get_db),
) -> RuleResponse:
    """Create a new transaction rule.

    Args:
        rule_data: Rule data
        db: Database session

    Returns:
        Created rule
    """
    service = RuleService(db)
    rule = service.create_rule(
        name=rule_data.name,
        description=rule_data.description,
        priority=rule_data.priority,
        conditions=rule_data.conditions,
        actions=rule_data.actions,
        is_active=rule_data.is_active,
    )
    return RuleResponse.from_model(rule)


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
) -> RuleResponse:
    """Get a specific rule.

    Args:
        rule_id: Rule ID
        db: Database session

    Returns:
        Rule details

    Raises:
        HTTPException: 404 if rule not found
    """
    service = RuleService(db)
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    return RuleResponse.from_model(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: Session = Depends(get_db),
) -> RuleResponse:
    """Update a rule.

    Args:
        rule_id: Rule ID
        rule_data: Updated rule data
        db: Database session

    Returns:
        Updated rule

    Raises:
        HTTPException: 404 if rule not found
    """
    service = RuleService(db)
    update_dict = rule_data.model_dump(exclude_unset=True)
    rule = service.update_rule(rule_id, **update_dict)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    return RuleResponse.from_model(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a rule.

    Args:
        rule_id: Rule ID
        db: Database session

    Raises:
        HTTPException: 404 if rule not found
    """
    service = RuleService(db)
    if not service.delete_rule(rule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
