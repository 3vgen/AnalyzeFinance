"""Модель бюджета (см. [[Бюджет]])."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testfinance.db.base import Base
from testfinance.models.base import TimestampMixin, UuidPk

if TYPE_CHECKING:
    from testfinance.models.category import Category


class Budget(TimestampMixin, Base):
    """Лимит расхода на категорию (с подкатегориями) за календарный месяц."""

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint(
            "owner_id", "category_id", "period", name="uq_budget_owner_cat_period"
        ),
    )

    id: Mapped[UuidPk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    #: Первое число месяца, на который задан лимит.
    period: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    #: Плановый лимит расхода за месяц.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False
    )

    category: Mapped[Category] = relationship("Category")
