"""Роутер аналитики (см. [[Методы и метрики]])."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.db.session import get_session
from testfinance.models.user import User
from testfinance.schemas.analytics import (
    CashflowPoint,
    CategoryExpense,
    Granularity,
    MetricsRead,
)
from testfinance.services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/cashflow", response_model=list[CashflowPoint])
async def cashflow(
    granularity: Granularity = Granularity.MONTH,
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CashflowPoint]:
    return await analytics.cashflow(
        session, current_user.id, granularity, date_from=date_from, date_to=date_to
    )


@router.get("/expenses", response_model=list[CategoryExpense])
async def expenses(
    rollup: bool = Query(default=True),
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CategoryExpense]:
    return await analytics.expenses_by_category(
        session, current_user.id, date_from=date_from, date_to=date_to, rollup=rollup
    )


@router.get("/metrics", response_model=MetricsRead)
async def metrics(
    date_from: date | None = None,
    date_to: date | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MetricsRead:
    return await analytics.metrics(
        session, current_user.id, date_from=date_from, date_to=date_to
    )
