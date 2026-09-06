"""Роутер счетов (см. [[Счёт]]): CRUD владельца."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.db.session import get_session
from testfinance.models.user import User
from testfinance.schemas.account import AccountCreate, AccountRead, AccountUpdate
from testfinance.services import accounts

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountRead])
async def list_accounts(
    include_archived: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AccountRead]:
    result = await accounts.list_accounts(
        session, current_user.id, include_archived=include_archived
    )
    return [AccountRead.model_validate(a) for a in result]


@router.post("", response_model=AccountRead, status_code=201)
async def create_account(
    payload: AccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountRead:
    account = await accounts.create_account(session, current_user.id, payload)
    return AccountRead.model_validate(account)


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountRead:
    account = await accounts.get_account(session, account_id, current_user.id)
    return AccountRead.model_validate(account)


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountRead:
    account = await accounts.update_account(
        session, account_id, current_user.id, payload
    )
    return AccountRead.model_validate(account)


@router.delete("/{account_id}", response_model=AccountRead)
async def archive_account(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AccountRead:
    """Архивирует счёт (мягкое удаление, см. [[Модель данных]])."""
    account = await accounts.archive_account(session, account_id, current_user.id)
    return AccountRead.model_validate(account)
