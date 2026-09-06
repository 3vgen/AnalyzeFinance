"""Сервис бюджетов (см. [[Бюджет]]): лимит категории на месяц, план/факт."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.models.budget import Budget
from testfinance.models.category import Category
from testfinance.models.transaction import Transaction
from testfinance.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate


def _month_start(period: date) -> date:
    return period.replace(day=1)


def _next_month(period: date) -> date:
    if period.month == 12:
        return date(period.year + 1, 1, 1)
    return date(period.year, period.month + 1, 1)


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


async def _category_and_descendants(
    session: AsyncSession, category_id: uuid.UUID, owner_id: uuid.UUID
) -> set[uuid.UUID]:
    """Множество id категории и всех её подкатегорий."""
    rows = (
        await session.execute(
            select(Category.id, Category.parent_id).where(
                Category.owner_id == owner_id
            )
        )
    ).all()
    children: dict[uuid.UUID, list[uuid.UUID]] = {}
    for cid, pid in rows:
        if pid is not None:
            children.setdefault(pid, []).append(cid)
    out: set[uuid.UUID] = set()
    stack = [category_id]
    while stack:
        node = stack.pop()
        if node in out:
            continue
        out.add(node)
        stack.extend(children.get(node, []))
    return out


async def _spent_for_categories(
    session: AsyncSession,
    owner_id: uuid.UUID,
    ids: set[uuid.UUID],
    period: date,
) -> Decimal:
    """Сумма расходов по категориям за месяц (включая подкатегории)."""
    if not ids:
        return Decimal("0")
    start = _month_start(period)
    end = _next_month(period)
    stmt = select(Transaction.amount).where(
        Transaction.owner_id == owner_id,
        Transaction.amount < 0,
        Transaction.is_archived.is_(False),
        Transaction.category_id.in_(ids),
        Transaction.occurred_on >= start,
        Transaction.occurred_on < end,
    )
    result = await session.execute(stmt)
    return -sum((row[0] for row in result), Decimal("0"))


async def _to_read(
    session: AsyncSession, budget: Budget, owner_id: uuid.UUID
) -> BudgetRead:
    ids = await _category_and_descendants(session, budget.category_id, owner_id)
    spent = await _spent_for_categories(session, owner_id, ids, budget.period)
    remaining = budget.amount - spent
    category = await session.get(Category, budget.category_id)
    return BudgetRead(
        id=budget.id,
        owner_id=budget.owner_id,
        category_id=budget.category_id,
        category_name=category.name if category else None,
        category_kind=category.kind if category else None,
        period=budget.period,
        planned=budget.amount,
        spent=spent,
        remaining=remaining,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )


async def list_budgets(
    session: AsyncSession,
    owner_id: uuid.UUID,
    period: date | None = None,
) -> list[BudgetRead]:
    stmt = select(Budget).where(Budget.owner_id == owner_id)
    if period is not None:
        stmt = stmt.where(Budget.period == _month_start(period))
    stmt = stmt.order_by(Budget.period)
    budgets = (await session.execute(stmt)).scalars().all()
    return [await _to_read(session, b, owner_id) for b in budgets]


async def get_budget(
    session: AsyncSession, budget_id: uuid.UUID, owner_id: uuid.UUID
) -> BudgetRead:
    budget = await session.get(Budget, budget_id)
    if budget is None or budget.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бюджет не найден",
        )
    return await _to_read(session, budget, owner_id)


async def create_budget(
    session: AsyncSession, owner_id: uuid.UUID, payload: BudgetCreate
) -> BudgetRead:
    category = await _get_owned_category(session, payload.category_id, owner_id)
    period = _month_start(payload.period)
    existing = await session.execute(
        select(Budget).where(
            Budget.owner_id == owner_id,
            Budget.category_id == category.id,
            Budget.period == period,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бюджет на эту категорию и месяц уже существует",
        )
    budget = Budget(
        owner_id=owner_id,
        category_id=category.id,
        period=period,
        amount=payload.amount,
    )
    session.add(budget)
    await session.commit()
    await session.refresh(budget)
    return await _to_read(session, budget, owner_id)


async def update_budget(
    session: AsyncSession,
    budget_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: BudgetUpdate,
) -> BudgetRead:
    budget = await session.get(Budget, budget_id)
    if budget is None or budget.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бюджет не найден",
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(budget, field, value)
    await session.commit()
    await session.refresh(budget)
    return await _to_read(session, budget, owner_id)


async def delete_budget(
    session: AsyncSession, budget_id: uuid.UUID, owner_id: uuid.UUID
) -> None:
    budget = await session.get(Budget, budget_id)
    if budget is None or budget.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бюджет не найден",
        )
    await session.delete(budget)
    await session.commit()
