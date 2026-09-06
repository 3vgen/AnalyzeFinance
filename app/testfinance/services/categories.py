"""Сервис категорий (см. [[Категория]]): дерево владельца."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.models.category import Category
from testfinance.models.enums import CategoryKind
from testfinance.schemas.category import CategoryCreate, CategoryUpdate


async def _get_owned_category(
    session: AsyncSession, category_id: uuid.UUID, owner_id: uuid.UUID
) -> Category:
    category = await session.get(Category, category_id)
    if category is None or category.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена",
        )
    return category


async def _get_owned_subtree_ids(
    session: AsyncSession, root_id: uuid.UUID, owner_id: uuid.UUID
) -> set[uuid.UUID]:
    """Все id в поддереве root (включая root) — для защиты от циклов."""
    result = await session.execute(
        select(Category.id, Category.parent_id).where(Category.owner_id == owner_id)
    )
    children: dict[uuid.UUID, list[uuid.UUID]] = {}
    for cid, pid in result:
        if pid is not None:
            children.setdefault(pid, []).append(cid)

    subtree: set[uuid.UUID] = set()
    stack = [root_id]
    while stack:
        node = stack.pop()
        if node in subtree:
            continue
        subtree.add(node)
        stack.extend(children.get(node, []))
    return subtree


async def _validate_parent(
    session: AsyncSession,
    owner_id: uuid.UUID,
    parent_id: uuid.UUID | None,
    kind: CategoryKind,
    self_id: uuid.UUID | None = None,
) -> None:
    if parent_id is None:
        return
    parent = await _get_owned_category(session, parent_id, owner_id)
    if parent.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нельзя вложить в заархивированную категорию",
        )
    if parent.kind != kind:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Родитель и ребёнок должны быть одного типа (income/expense)",
        )
    if self_id is not None and parent_id == self_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Категория не может быть родителем самой себе",
        )
    if self_id is not None:
        subtree = await _get_owned_subtree_ids(session, self_id, owner_id)
        if parent_id in subtree:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Нельзя перенести категорию внутрь собственного поддерева",
            )


async def list_categories(
    session: AsyncSession,
    owner_id: uuid.UUID,
    include_archived: bool = False,
) -> list[Category]:
    stmt = select(Category).where(Category.owner_id == owner_id)
    if not include_archived:
        stmt = stmt.where(Category.is_archived.is_(False))
    stmt = stmt.order_by(Category.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_category(
    session: AsyncSession, category_id: uuid.UUID, owner_id: uuid.UUID
) -> Category:
    return await _get_owned_category(session, category_id, owner_id)


async def create_category(
    session: AsyncSession, owner_id: uuid.UUID, payload: CategoryCreate
) -> Category:
    await _validate_parent(
        session, owner_id, payload.parent_id, kind=payload.kind
    )
    category = Category(
        owner_id=owner_id,
        name=payload.name,
        kind=payload.kind.value,
        parent_id=payload.parent_id,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def update_category(
    session: AsyncSession,
    category_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: CategoryUpdate,
) -> Category:
    category = await _get_owned_category(session, category_id, owner_id)
    if category.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Заархивированную категорию нельзя изменять",
        )
    data = payload.model_dump(exclude_unset=True)
    if "parent_id" in data:
        await _validate_parent(
            session,
            owner_id,
            data["parent_id"],
            kind=category.kind,
            self_id=category.id,
        )
    for field, value in data.items():
        setattr(category, field, value)
    await session.commit()
    await session.refresh(category)
    return category


async def archive_category(
    session: AsyncSession, category_id: uuid.UUID, owner_id: uuid.UUID
) -> Category:
    category = await _get_owned_category(session, category_id, owner_id)
    category.is_archived = True
    await session.commit()
    await session.refresh(category)
    return category
