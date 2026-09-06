"""Роутер категорий (см. [[Категория]])."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.db.session import get_session
from testfinance.models.user import User
from testfinance.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from testfinance.services import categories

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    include_archived: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CategoryRead]:
    result = await categories.list_categories(
        session, current_user.id, include_archived=include_archived
    )
    return [CategoryRead.model_validate(c) for c in result]


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CategoryRead:
    category = await categories.create_category(session, current_user.id, payload)
    return CategoryRead.model_validate(category)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CategoryRead:
    category = await categories.get_category(session, category_id, current_user.id)
    return CategoryRead.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CategoryRead:
    category = await categories.update_category(
        session, category_id, current_user.id, payload
    )
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", response_model=CategoryRead)
async def archive_category(
    category_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CategoryRead:
    category = await categories.archive_category(session, category_id, current_user.id)
    return CategoryRead.model_validate(category)
