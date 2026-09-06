"""Сервис финансовых целей (см. [[Финансовые цели]])."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.models.financial_goal import FinancialGoal
from testfinance.schemas.goal import GoalCreate, GoalRead, GoalUpdate


def _progress_percent(goal: FinancialGoal) -> float:
    if goal.target_amount <= 0:
        return 0.0
    value = float(goal.current_amount) / float(goal.target_amount) * 100
    return min(max(value, 0.0), 100.0)


def _to_read(goal: FinancialGoal) -> GoalRead:
    return GoalRead(
        id=goal.id,
        owner_id=goal.owner_id,
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date,
        progress_percent=_progress_percent(goal),
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


async def _get_owned_goal(
    session: AsyncSession, goal_id: uuid.UUID, owner_id: uuid.UUID
) -> FinancialGoal:
    goal = await session.get(FinancialGoal, goal_id)
    if goal is None or goal.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Цель не найдена",
        )
    return goal


async def list_goals(session: AsyncSession, owner_id: uuid.UUID) -> list[GoalRead]:
    stmt = select(FinancialGoal).where(FinancialGoal.owner_id == owner_id)
    stmt = stmt.order_by(FinancialGoal.created_at)
    goals = (await session.execute(stmt)).scalars().all()
    return [_to_read(g) for g in goals]


async def get_goal(
    session: AsyncSession, goal_id: uuid.UUID, owner_id: uuid.UUID
) -> GoalRead:
    return _to_read(await _get_owned_goal(session, goal_id, owner_id))


async def create_goal(
    session: AsyncSession, owner_id: uuid.UUID, payload: GoalCreate
) -> GoalRead:
    goal = FinancialGoal(
        owner_id=owner_id,
        name=payload.name,
        target_amount=payload.target_amount,
        current_amount=payload.current_amount,
        target_date=payload.target_date,
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return _to_read(goal)


async def update_goal(
    session: AsyncSession,
    goal_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: GoalUpdate,
) -> GoalRead:
    goal = await _get_owned_goal(session, goal_id, owner_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(goal, field, value)
    await session.commit()
    await session.refresh(goal)
    return _to_read(goal)


async def delete_goal(
    session: AsyncSession, goal_id: uuid.UUID, owner_id: uuid.UUID
) -> None:
    goal = await _get_owned_goal(session, goal_id, owner_id)
    await session.delete(goal)
    await session.commit()
