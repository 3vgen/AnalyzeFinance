"""Модель транзакции (см. [[Транзакция]])."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testfinance.db.base import Base
from testfinance.models.base import Money, TimestampMixin, UuidPk

if TYPE_CHECKING:
    from testfinance.models.account import Account
    from testfinance.models.category import Category


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # Дедупликация импорта (см. [[Импорт выписок]]): уникальный внешний ключ источника.
        Index(
            "uq_transactions_account_external",
            "account_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    id: Mapped[UuidPk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code"), nullable=False
    )
    #: Сумма в валюте операции (ADR-004): положительная — доход, отрицательная — расход.
    amount: Mapped[Money]
    #: Дата операции (из выписки). created_at — время записи в БД.
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    #: Внешний идентификатор из источника (банк/CSV) для дедупликации импорта.
    external_id: Mapped[str | None] = mapped_column(String(100))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    account: Mapped[Account] = relationship("Account")
    category: Mapped[Category | None] = relationship("Category")
