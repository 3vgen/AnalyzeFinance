"""Модель счёта (см. [[Счёт]])."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testfinance.db.base import Base
from testfinance.models.base import TimestampMixin, UuidPk
from testfinance.models.enums import AccountType

if TYPE_CHECKING:
    from testfinance.models.currency import Currency


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[UuidPk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[AccountType] = mapped_column(
        String(20), default=AccountType.CHECKING.value, nullable=False
    )
    currency_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), nullable=False
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    #: Открытый остаток для выверки; актуальный баланс считается по транзакциям.
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4),
        nullable=False,
        server_default=text("0"),
    )

    currency: Mapped[Currency] = relationship("Currency")
