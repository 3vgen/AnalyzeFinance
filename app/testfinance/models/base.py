"""Общие типы колонок и миксины моделей (SQLAlchemy 2.0, стиль Annotated)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from sqlalchemy import DateTime, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

#: Первичный ключ UUID с генерацией на стороне приложения.
UuidPk = Annotated[
    uuid.UUID,
    mapped_column(Uuid, primary_key=True, default=uuid.uuid4),
]

#: Денежная сумма (ADR-004): NUMERIC(19,4), не NULL.
Money = Annotated[
    Decimal,
    mapped_column(Numeric(precision=19, scale=4), nullable=False),
]


class TimestampMixin:
    """Служебные метки created_at/updated_at (UTC)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
