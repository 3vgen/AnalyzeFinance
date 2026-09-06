"""Pydantic-схемы финансовых целей (см. [[Финансовые цели]])."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0)
    target_date: date | None = None


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_amount: Decimal | None = Field(default=None, gt=0)
    current_amount: Decimal | None = Field(default=None, ge=0)
    target_date: date | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None
    progress_percent: float = 0.0
    created_at: datetime
    updated_at: datetime
