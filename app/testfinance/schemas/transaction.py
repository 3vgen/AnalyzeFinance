"""Pydantic-схемы транзакций (см. [[Транзакция]])."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from testfinance.models.enums import CategoryKind


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0)  # положительная сумма
    kind: CategoryKind  # направление операции: доход/расход
    currency_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    occurred_on: date
    description: str | None = Field(default=None, max_length=500)


class TransactionUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    kind: CategoryKind | None = None
    currency_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    occurred_on: date | None = None
    description: str | None = Field(default=None, max_length=500)


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    currency_code: str
    amount: Decimal  # знак: + доход, − расход (ADR-004)
    occurred_on: date
    description: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
