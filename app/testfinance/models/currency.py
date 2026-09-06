"""Справочник валют и исторические курсы (см. [[Валюты]])."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from testfinance.db.base import Base
from testfinance.models.base import TimestampMixin


class Currency(Base):
    """Каталог валют по ISO 4217. Естественный ключ — код (ADR-005)."""

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(10))
    exponent: Mapped[int] = mapped_column(SmallInteger, default=2, nullable=False)


class ExchangeRate(Base):
    """Курс base→quote на дату (сколько quote стоит 1 base), ADR-004."""

    __tablename__ = "exchange_rates"
    __table_args__ = (
        CheckConstraint("rate > 0", name="rate_positive"),
        CheckConstraint("base_code != quote_code", name="base_not_quote"),
    )

    base_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), primary_key=True
    )
    quote_code: Mapped[str] = mapped_column(
        String(3), ForeignKey("currencies.code"), primary_key=True
    )
    rate_date: Mapped[date] = mapped_column(Date, primary_key=True)
    rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), nullable=False
    )
