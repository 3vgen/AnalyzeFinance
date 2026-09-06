"""Роутер финансовых целей (см. [[Финансовые цели]])."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.db.session import get_session
from testfinance.models.user import User
from testfinance.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from testfinance.services import goals

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalRead])
async def list_goals(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[GoalRead]:
    return await goals.list_goals(session, current_user.id)


@router.post("", response_model=GoalRead, status_code=201)
async def create_goal(
    payload: GoalCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    return await goals.create_goal(session, current_user.id, payload)


@router.get("/{goal_id}", response_model=GoalRead)
async def get_goal(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    return await goals.get_goal(session, goal_id, current_user.id)


@router.patch("/{goal_id}", response_model=GoalRead)
async def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    return await goals.update_goal(session, goal_id, current_user.id, payload)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    await goals.delete_goal(session, goal_id, current_user.id)
