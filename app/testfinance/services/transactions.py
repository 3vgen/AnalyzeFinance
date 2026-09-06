"""Сервис транзакций (см. [[Транзакция]]): CRUD владельца."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.models.account import Account
from testfinance.models.category import Category
from testfinance.models.enums import CategoryKind
from testfinance.models.transaction import Transaction
from testfinance.schemas.transaction import TransactionCreate, TransactionUpdate


def _signed_amount(amount: Decimal, kind: CategoryKind) -> Decimal:
    """Знак суммы по направлению: доход положительный, расход отрицательный."""
    if kind == CategoryKind.INCOME:
        return abs(amount)
    return -abs(amount)


async def _get_owned_account(
    session: AsyncSession, account_id: uuid.UUID, owner_id: uuid.UUID
) -> Account:
    account = await session.get(Account, account_id)
    if account is None or account.owner_id != owner_id or account.is_archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Счёт не найден или заархивирован",
        )
    return account


async def _validate_category(
    session: AsyncSession,
    category_id: uuid.UUID | None,
    owner_id: uuid.UUID,
) -> None:
    if category_id is None:
        return
    category = await session.get(Category, category_id)
    if category is None or category.owner_id != owner_id or category.is_archived:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Категория не найдена, не принадлежит пользователю или заархивирована",
        )


async def list_transactions(
    session: AsyncSession,
    owner_id: uuid.UUID,
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    kind: CategoryKind | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.owner_id == owner_id)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)
    if kind is not None:
        if kind == CategoryKind.INCOME:
            stmt = stmt.where(Transaction.amount > 0)
        else:
            stmt = stmt.where(Transaction.amount < 0)
    if date_from is not None:
        stmt = stmt.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        stmt = stmt.where(Transaction.occurred_on <= date_to)
    stmt = stmt.order_by(Transaction.occurred_on.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_transaction(
    session: AsyncSession, transaction_id: uuid.UUID, owner_id: uuid.UUID
) -> Transaction:
    transaction = await session.get(Transaction, transaction_id)
    if transaction is None or transaction.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена",
        )
    return transaction


async def create_transaction(
    session: AsyncSession, owner_id: uuid.UUID, payload: TransactionCreate
) -> Transaction:
    account = await _get_owned_account(session, payload.account_id, owner_id)
    await _validate_category(session, payload.category_id, owner_id)

    currency_code = payload.currency_code or account.currency_code
    transaction = Transaction(
        owner_id=owner_id,
        account_id=account.id,
        category_id=payload.category_id,
        currency_code=currency_code,
        amount=_signed_amount(payload.amount, payload.kind),
        occurred_on=payload.occurred_on,
        description=payload.description,
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


async def update_transaction(
    session: AsyncSession,
    transaction_id: uuid.UUID,
    owner_id: uuid.UUID,
    payload: TransactionUpdate,
) -> Transaction:
    transaction = await get_transaction(session, transaction_id, owner_id)
    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data:
        await _validate_category(session, data["category_id"], owner_id)
    if "currency_code" in data and data["currency_code"] is not None:
        if data["currency_code"] != transaction.currency_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Смена валюты транзакции не поддерживается",
            )

    kind = data.pop("kind", None)
    if kind is not None:
        amount = data.pop("amount", None)
        base = amount if amount is not None else abs(transaction.amount)
        transaction.amount = _signed_amount(base, kind)
    elif "amount" in data:
        existing_kind = (
            CategoryKind.INCOME if transaction.amount > 0 else CategoryKind.EXPENSE
        )
        transaction.amount = _signed_amount(data.pop("amount"), existing_kind)

    for field, value in data.items():
        setattr(transaction, field, value)

    await session.commit()
    await session.refresh(transaction)
    return transaction


async def archive_transaction(
    session: AsyncSession, transaction_id: uuid.UUID, owner_id: uuid.UUID
) -> Transaction:
    transaction = await get_transaction(session, transaction_id, owner_id)
    transaction.is_archived = True
    await session.commit()
    await session.refresh(transaction)
    return transaction
