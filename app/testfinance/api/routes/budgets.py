"""Роутер бюджетов (см. [[Бюджет]]): лимит категории × месяц, план/факт."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.db.session import get_session
from testfinance.models.user import User
from testfinance.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from testfinance.services import budgets

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetRead])
async def list_budgets(
    period: date | None = Query(default=None, description="Первый день месяца"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[BudgetRead]:
    return await budgets.list_budgets(session, current_user.id, period=period)


@router.post("", response_model=BudgetRead, status_code=201)
async def create_budget(
    payload: BudgetCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetRead:
    return await budgets.create_budget(session, current_user.id, payload)


@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(
    budget_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetRead:
    return await budgets.get_budget(session, budget_id, current_user.id)


@router.patch("/{budget_id}", response_model=BudgetRead)
async def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetRead:
    return await budgets.update_budget(session, budget_id, current_user.id, payload)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    await budgets.delete_budget(session, budget_id, current_user.id)
