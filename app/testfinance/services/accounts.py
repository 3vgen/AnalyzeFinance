"""Сервис счетов (см. [[Счёт]]): CRUD с изоляцией по владельцу."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.models.account import Account
from testfinance.models.currency import Currency
from testfinance.schemas.account import AccountCreate, AccountUpdate


async def _ensure_currency_exists(session: AsyncSession, code: str) -> None:
    exists = await session.get(Currency, code)
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Валюта '{code}' не найдена",
        )


async def _get_owned_account(
    session: AsyncSession, account_id: uuid.UUID, owner_id: uuid.UUID
) -> Account:
    account = await session.get(Account, account_id)
    if account is None or account.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счёт не найден",
        )
    return account


async def list_accounts(
    session: AsyncSession,
    owner_id: uuid.UUID,
    include_archived: bool = False,
) -> list[Account]:
    stmt = select(Account).where(Account.owner_id == owner_id)
    if not include_archived:
        stmt = stmt.where(Account.is_archived.is_(False))
    stmt = stmt.order_by(Account.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_account(
    session: AsyncSession, account_id: uuid.UUID, owner_id: uuid.UUID
) -> Account:
    return await _get_owned_account(session, account_id, owner_id)


async def create_account(
    session: AsyncSession, owner_id: uuid.UUID, payload: AccountCreate
) -> Account:
    await _ensure_currency_exists(session, payload.currency_code)
    account = Account(
        owner_id=owner_id,
        name=payload.name,
        type=payload.type.value,
        currency_code=payload.currency_code,
        opening_balance=payload.opening_balance,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


async def update_account(
    session: AsyncSession,
    account_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: AccountUpdate,
) -> Account:
    account = await _get_owned_account(session, account_id, owner_id)
    if account.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Заархивированный счёт нельзя изменять",
        )
    data = payload.model_dump(exclude_unset=True)
    if "type" in data and data["type"] is not None:
        data["type"] = data["type"].value
    for field, value in data.items():
        setattr(account, field, value)
    await session.commit()
    await session.refresh(account)
    return account


async def archive_account(
    session: AsyncSession, account_id: uuid.UUID, owner_id: uuid.UUID
) -> Account:
    account = await _get_owned_account(session, account_id, owner_id)
    account.is_archived = True
    await session.commit()
    await session.refresh(account)
    return account
