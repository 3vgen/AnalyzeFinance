"""Сервис аналитики (см. [[Методы и метрики]]).

Внимание: суммы считаются по каждой валюте отдельно (ADR-004) — без пересчёта
курсов. Сводка в разных валютах возможна после реализации конвертации (этап 3).
"""

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from testfinance.models.account import Account
from testfinance.models.category import Category
from testfinance.models.enums import AccountType
from testfinance.models.transaction import Transaction
from testfinance.schemas.analytics import (
    CashflowPoint,
    CategoryExpense,
    Granularity,
    MetricsByCurrency,
    MetricsRead,
)

# Типы счетов, участвующие в ликвидных активах ([[Финансовая подушка]]).
LIQUID_TYPES = {
    AccountType.CHECKING,
    AccountType.SAVINGS,
    AccountType.CASH,
}


def _bucket(day: date, granularity: Granularity) -> date:
    """Начало периода для дня."""
    if granularity == Granularity.DAY:
        return day
    if granularity == Granularity.WEEK:
        return day - timedelta(days=day.isoweekday() - 1)
    return day.replace(day=1)


async def cashflow(
    session: AsyncSession,
    owner_id: uuid.UUID,
    granularity: Granularity,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[CashflowPoint]:
    """Кэшфлоу по периодам в разрезе валют (см. [[Кэшфлоу]])."""
    stmt = select(Transaction).where(
        Transaction.owner_id == owner_id, Transaction.is_archived.is_(False)
    )
    if date_from is not None:
        stmt = stmt.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        stmt = stmt.where(Transaction.occurred_on <= date_to)
    rows = (await session.execute(stmt)).scalars()

    inc: dict[date, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    exp: dict[date, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for t in rows:
        key = _bucket(t.occurred_on, granularity)
        if t.amount > 0:
            inc[key][t.currency_code] += t.amount
        elif t.amount < 0:
            exp[key][t.currency_code] += abs(t.amount)

    points: list[CashflowPoint] = []
    for period in sorted(set(inc) | set(exp)):
        for currency in sorted(set(inc[period]) | set(exp[period])):
            income = inc[period].get(currency, Decimal("0"))
            expense = exp[period].get(currency, Decimal("0"))
            points.append(
                CashflowPoint(
                    period=period,
                    currency_code=currency,
                    income=income,
                    expense=expense,
                    net=income - expense,
                )
            )
    return points


async def _category_map(
    session: AsyncSession, owner_id: uuid.UUID
) -> tuple[dict[uuid.UUID, Category], dict[uuid.UUID, uuid.UUID | None]]:
    """Все категории владельца: {id: cat} и {id: id корня}."""
    rows = (await session.execute(select(Category).where(Category.owner_id == owner_id))).scalars()
    cat_by_id = {c.id: c for c in rows}

    def root_of(cat_id: uuid.UUID | None) -> uuid.UUID | None:
        seen: set[uuid.UUID] = set()
        cur = cat_by_id.get(cat_id) if cat_id else None
        while cur is not None and cur.parent_id is not None and cur.id not in seen:
            seen.add(cur.id)
            cur = cat_by_id.get(cur.parent_id)
        return cur.id if cur is not None else None

    root_by_id = {cid: root_of(cid) for cid in cat_by_id}
    return cat_by_id, root_by_id


async def expenses_by_category(
    session: AsyncSession,
    owner_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    rollup: bool = True,
) -> list[CategoryExpense]:
    """Расходы по категориям (см. [[Анализ расходов]]).

    rollup=True: суммы дочерних категорий включаются в корневые.
    """
    cat_by_id, root_by_id = await _category_map(session, owner_id)

    stmt = select(Transaction.category_id, Transaction.currency_code, Transaction.amount).where(
        Transaction.owner_id == owner_id,
        Transaction.amount < 0,
        Transaction.is_archived.is_(False),
    )
    if date_from is not None:
        stmt = stmt.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        stmt = stmt.where(Transaction.occurred_on <= date_to)
    rows = await session.execute(stmt)

    acc: dict[tuple[uuid.UUID | None, str], Decimal] = defaultdict(Decimal)
    for cat_id, currency, amount in rows:
        key = (root_by_id.get(cat_id) if (rollup and cat_id) else cat_id, currency)
        acc[key] += abs(amount)

    out: list[CategoryExpense] = []
    for (cat_id, currency), amount in sorted(
        acc.items(), key=lambda kv: (kv[0][0] is not None, str(kv[0][0]), kv[0][1])
    ):
        name = cat_by_id[cat_id].name if cat_id in cat_by_id else None
        out.append(
            CategoryExpense(
                category_id=cat_id, name=name, currency_code=currency, amount=amount
            )
        )
    return out


async def metrics(
    session: AsyncSession,
    owner_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> MetricsRead:
    """Сводные метрики по валютам (см. [[Методы и метрики]]).

    - сберегательная норма = net / income за период;
    - чистый капитал = суммарные остатки счетов (по валютам, без конвертации);
    - ликвидные активы и подушка в месяцах.
    """
    window_months = _window_months(date_from, date_to)

    # Доходы/расходы за окно.
    tx_stmt = select(
        Transaction.currency_code, Transaction.amount
    ).where(Transaction.owner_id == owner_id, Transaction.is_archived.is_(False))
    if date_from is not None:
        tx_stmt = tx_stmt.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        tx_stmt = tx_stmt.where(Transaction.occurred_on <= date_to)
    tx_rows = (await session.execute(tx_stmt)).all()

    income: dict[str, Decimal] = defaultdict(Decimal)
    expense: dict[str, Decimal] = defaultdict(Decimal)
    for currency, amount in tx_rows:
        if amount > 0:
            income[currency] += amount
        elif amount < 0:
            expense[currency] += abs(amount)

    # Остатки счетов и их движение (для чистого капитала и ликвидности).
    acc_rows = (
        await session.execute(
            select(
                Account.id,
                Account.type,
                Account.currency_code,
                Account.opening_balance,
            ).where(Account.owner_id == owner_id, Account.is_archived.is_(False))
        )
    ).all()

    # Тип и валюта счетов владельца.
    type_by_id: dict[uuid.UUID, AccountType] = {}
    acc_currency: dict[uuid.UUID, str] = {}
    for aid, atype, ccode, _obal in acc_rows:
        type_by_id[aid] = AccountType(atype)
        acc_currency[aid] = ccode

    # Движения по счетам владельца (без оконного фильтра — остатки накопленные).
    flow_stmt = select(
        Transaction.account_id, Transaction.amount
    ).where(Transaction.owner_id == owner_id, Transaction.is_archived.is_(False))
    flow = defaultdict(Decimal)
    for aid, amount in (await session.execute(flow_stmt)).all():
        flow[aid] += amount

    net_worth: dict[str, Decimal] = defaultdict(Decimal)
    liquid: dict[str, Decimal] = defaultdict(Decimal)
    for aid, atype, ccode, obal in acc_rows:
        total = obal + flow.get(aid, Decimal("0"))
        net_worth[ccode] += total
        if atype in LIQUID_TYPES:
            liquid[ccode] += total

    currencies = sorted(set(income) | set(expense) | set(net_worth))
    metrics_list: list[MetricsByCurrency] = []
    for currency in currencies:
        inc = income.get(currency, Decimal("0"))
        exp = expense.get(currency, Decimal("0"))
        net = inc - exp
        savings_rate = net / inc if inc > 0 else None
        liquid_assets = liquid.get(currency)
        net_worth_val = net_worth.get(currency)
        avg_monthly_expense = (
            exp / window_months if (window_months and window_months > 0) else None
        )
        cushion = (
            liquid_assets / avg_monthly_expense
            if liquid_assets is not None
            and avg_monthly_expense
            and avg_monthly_expense > 0
            else None
        )
        metrics_list.append(
            MetricsByCurrency(
                currency_code=currency,
                income=inc,
                expense=exp,
                net=net,
                savings_rate=savings_rate,
                net_worth=net_worth_val,
                liquid_assets=liquid_assets,
                cushion_months=cushion,
            )
        )

    return MetricsRead(
        currency_code=None,
        date_from=date_from,
        date_to=date_to,
        generated_at=datetime.now(timezone.utc),
        metrics=metrics_list,
    )


def _window_months(date_from: date | None, date_to: date | None) -> Decimal | None:
    """Число месяцев в окне; None, если окно не задано или короче месяца."""
    today = date.today()
    start = date_from or today.replace(day=1)
    end = date_to or today
    if end < start or (end - start).days < 28:
        return None
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    return Decimal(months)
