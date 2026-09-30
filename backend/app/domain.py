from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Txn:
    posted_on: date
    merchant: str
    amount: Decimal
    category: str


@dataclass(frozen=True)
class CategoryTotal:
    category: str
    amount: Decimal
    delta: Decimal | None


@dataclass(frozen=True)
class RecurringItem:
    merchant: str
    category: str
    monthly_amount: Decimal
    annual_amount: Decimal
    first_seen: date
    last_seen: date
    occurrences: int
    total_spent: Decimal
    previous_amount: Decimal | None
    flags: tuple[str, ...]


@dataclass(frozen=True)
class LargeTransaction:
    posted_on: date
    merchant: str
    amount: Decimal
    category: str


@dataclass(frozen=True)
class Autopsy:
    month: str
    month_label: str
    income: Decimal
    spending: Decimal
    remaining: Decimal
    categories: list[CategoryTotal]
    previous_month: str | None
    previous_label: str | None
    spending_delta: Decimal | None
    drivers: list[str]
    narrative: str
    recurring: list[RecurringItem]
    possible_new: list[RecurringItem]
    large_transactions: list[LargeTransaction]
