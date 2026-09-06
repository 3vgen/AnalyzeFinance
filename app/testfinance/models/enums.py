"""Перечисления предметной области (см. базу знаний, разделы 10/20)."""

from enum import Enum


class AccountType(str, Enum):
    """Тип счёта ([[Счёт]])."""

    CHECKING = "checking"  # расчётный/карточный
    SAVINGS = "savings"  # накопительный
    CASH = "cash"  # наличные
    CREDIT = "credit"  # кредитная карта / займ ([[Обязательства]])
    BROKERAGE = "brokerage"  # брокерский ([[Инвестиции]])
    OTHER = "other"


class CategoryKind(str, Enum):
    """Назначение категории ([[Категория]])."""

    INCOME = "income"  # категория дохода
    EXPENSE = "expense"  # категория расхода
