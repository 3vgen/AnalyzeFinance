"""Pydantic-схемы счёта (см. [[Счёт]])."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from testfinance.models.enums import AccountType


class AccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    type: AccountType = AccountType.CHECKING
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")


class AccountCreate(AccountBase):
    opening_balance: Decimal = Field(default=Decimal("0"), ge=0)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    type: AccountType | None = None
    opening_balance: Decimal | None = Field(default=None, ge=0)


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    is_archived: bool
    opening_balance: Decimal
    created_at: datetime
    updated_at: datetime
