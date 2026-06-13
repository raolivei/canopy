"""Pydantic models for transaction rules API."""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ConditionCreate(BaseModel):
    """Create rule condition."""

    field: str  # RuleConditionField enum
    operator: str  # RuleConditionOperator enum
    value: str
    numeric_value: Optional[Decimal] = None


class ActionCreate(BaseModel):
    """Create rule action."""

    action_type: str  # RuleActionType enum
    value: str
    order: int = 0
    split_config: Optional[dict] = None


class RuleCreate(BaseModel):
    """Create transaction rule."""

    name: str
    description: Optional[str] = None
    priority: int = 0
    is_active: bool = True
    conditions: Optional[List[ConditionCreate]] = None
    actions: Optional[List[ActionCreate]] = None


class RuleUpdate(BaseModel):
    """Update transaction rule."""

    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class ConditionResponse(BaseModel):
    """Rule condition response."""

    id: int
    field: str
    operator: str
    value: str
    numeric_value: Optional[Decimal] = None


class ActionResponse(BaseModel):
    """Rule action response."""

    id: int
    action_type: str
    value: str
    order: int
    split_config: Optional[dict] = None


class RuleResponse(BaseModel):
    """Transaction rule response."""

    id: int
    name: str
    description: Optional[str] = None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    conditions: List[ConditionResponse]
    actions: List[ActionResponse]

    @classmethod
    def from_model(cls, model):
        """Convert ORM model to Pydantic model."""
        return cls(
            id=model.id,
            name=model.name,
            description=model.description,
            priority=model.priority,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            conditions=[
                ConditionResponse(
                    id=c.id,
                    field=c.field,
                    operator=c.operator,
                    value=c.value,
                    numeric_value=c.numeric_value,
                )
                for c in model.conditions
            ],
            actions=[
                ActionResponse(
                    id=a.id,
                    action_type=a.action_type,
                    value=a.value,
                    order=a.order,
                    split_config=a.split_config,
                )
                for a in model.actions
            ],
        )

    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """List rules response."""

    total: int
    rules: List[RuleResponse]
