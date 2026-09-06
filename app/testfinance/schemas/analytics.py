"""Pydantic-схемы аналитики (см. [[Методы и метрики]])."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class Granularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class CashflowPoint(BaseModel):
    period: date
    currency_code: str
    income: Decimal
    expense: Decimal
    net: Decimal


class CategoryExpense(BaseModel):
    category_id: uuid.UUID | None
    name: str | None
    currency_code: str
    amount: Decimal


class MetricsByCurrency(BaseModel):
    currency_code: str
    income: Decimal = Decimal("0")
    expense: Decimal = Decimal("0")
    net: Decimal = Decimal("0")
    savings_rate: Decimal | None = None
    net_worth: Decimal | None = None
    liquid_assets: Decimal | None = None
    cushion_months: Decimal | None = None


class MetricsRead(BaseModel):
    currency_code: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    generated_at: datetime
    metrics: list[MetricsByCurrency]
