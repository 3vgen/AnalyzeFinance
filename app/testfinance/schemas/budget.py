"""Pydantic-схемы бюджета (см. [[Бюджет]])."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from testfinance.models.enums import CategoryKind


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    #: Первое число месяца (например, 2026-09-01).
    period: date
    amount: Decimal = Field(gt=0)


class BudgetUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)


class BudgetRead(BaseModel):
    """Бюджет с посчитанным фактом и остатком."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    category_id: uuid.UUID
    category_name: str | None = None
    category_kind: CategoryKind | None = None
    period: date
    planned: Decimal
    spent: Decimal = Decimal("0")
    remaining: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime
