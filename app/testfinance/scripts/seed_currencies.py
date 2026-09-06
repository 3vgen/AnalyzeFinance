"""Seed базовых валют (справочник [[Валюты]]).

Запуск: poetry run python -m testfinance.scripts.seed_currencies
"""

import asyncio

from sqlalchemy import select

from testfinance.db.session import SessionFactory
from testfinance.models.currency import Currency

BASE_CURRENCIES = [
    Currency(code="RUB", name="Российский рубль", symbol="₽", exponent=2),
    Currency(code="USD", name="Доллар США", symbol="$", exponent=2),
    Currency(code="EUR", name="Евро", symbol="€", exponent=2),
    Currency(code="GBP", name="Фунт стерлингов", symbol="£", exponent=2),
    Currency(code="CNY", name="Китайский юань", symbol="¥", exponent=2),
]


async def seed() -> int:
    added = 0
    async with SessionFactory() as session:
        existing = set((await session.execute(select(Currency.code))).scalars())
        for currency in BASE_CURRENCIES:
            if currency.code not in existing:
                session.add(currency)
                added += 1
        await session.commit()
    return added


def main() -> None:
    added = asyncio.run(seed())
    print(f"Валют добавлено: {added}. Всего базовых: {len(BASE_CURRENCIES)}")


if __name__ == "__main__":
    main()
