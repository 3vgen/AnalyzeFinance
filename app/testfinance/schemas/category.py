"""Pydantic-схемы категорий (см. [[Категория]])."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from testfinance.models.enums import CategoryKind


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    kind: CategoryKind
    parent_id: uuid.UUID | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    parent_id: uuid.UUID | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    kind: CategoryKind
    is_archived: bool
    created_at: datetime
    updated_at: datetime
