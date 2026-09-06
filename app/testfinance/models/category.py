"""Модель категории (см. [[Категория]])."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from testfinance.db.base import Base
from testfinance.models.base import TimestampMixin, UuidPk
from testfinance.models.enums import CategoryKind


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[UuidPk]
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    kind: Mapped[CategoryKind] = mapped_column(String(20), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    parent: Mapped[Category | None] = relationship(
        "Category", remote_side=lambda: [Category.id], back_populates="children"
    )
    children: Mapped[list[Category]] = relationship(
        "Category", back_populates="parent"
    )
