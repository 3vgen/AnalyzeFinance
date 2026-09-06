"""Роутер транзакций (см. [[Транзакция]])."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.api.deps import get_current_user
from testfinance.db.session import get_session
from testfinance.models.enums import CategoryKind
from testfinance.models.user import User
from testfinance.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from testfinance.services import transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    kind: CategoryKind | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TransactionRead]:
    result = await transactions.list_transactions(
        session,
        current_user.id,
        account_id=account_id,
        category_id=category_id,
        kind=kind,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return [TransactionRead.model_validate(t) for t in result]


@router.post("", response_model=TransactionRead, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    transaction = await transactions.create_transaction(
        session, current_user.id, payload
    )
    return TransactionRead.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    transaction = await transactions.get_transaction(
        session, transaction_id, current_user.id
    )
    return TransactionRead.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    transaction = await transactions.update_transaction(
        session, transaction_id, current_user.id, payload
    )
    return TransactionRead.model_validate(transaction)


@router.delete("/{transaction_id}", response_model=TransactionRead)
async def archive_transaction(
    transaction_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    """Архивирует транзакцию (мягкое удаление)."""
    transaction = await transactions.archive_transaction(
        session, transaction_id, current_user.id
    )
    return TransactionRead.model_validate(transaction)
