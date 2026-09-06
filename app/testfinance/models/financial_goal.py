"""Модель финансовой цели (см. [[Финансовые цели]])."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from testfinance.db.base import Base
from testfinance.models.base import TimestampMixin, UuidPk


class FinancialGoal(TimestampMixin, Base):
    """Цель с целевой суммой и сроком; прогресс обновляется вручную."""

    __tablename__ = "financial_goals"

    id: Mapped[UuidPk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )
    #: Сколько уже накоплено (вручную).
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=0
    )
    target_date: Mapped[date | None] = mapped_column(Date)
