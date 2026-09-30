from datetime import date
from decimal import Decimal

from app.domain import Txn

MONTHS = (6, 7, 8, 9)


def _on(month: int, day: int) -> date:
    return date(2026, month, day)


def _monthly(merchant: str, amount: str, day: int, months: tuple[int, ...] = MONTHS) -> list[Txn]:
    return [
        Txn(_on(month, day), merchant, Decimal(amount), "Subscriptions")
        for month in months
    ]


def _charges(rows: list[tuple[int, int, str, str, str]]) -> list[Txn]:
    return [Txn(_on(month, day), merchant, Decimal(amount), category) for month, day, merchant, amount, category in rows]


def sample_transactions() -> list[Txn]:
    """Four months of fake activity. September is the month that looks off."""
    transactions: list[Txn] = []
    for month in MONTHS:
        transactions.append(Txn(_on(month, 1), "Northwind Payroll", Decimal("4100.00"), "Income"))
        transactions.append(Txn(_on(month, 1), "Harbor Apartments", Decimal("-1450.00"), "Rent"))

    transactions.extend(_monthly("Spotify", "-11.99", 3))
    transactions.extend(_monthly("Netflix", "-15.49", 5, (6, 7, 8)))
    transactions.append(Txn(_on(9, 5), "Netflix", Decimal("-22.99"), "Subscriptions"))
    transactions.extend(_monthly("Adobe", "-29.99", 7))
    transactions.extend(_monthly("Apple iCloud", "-3.99", 8))
    transactions.extend(_monthly("Planet Fitness", "-49.99", 10))
    transactions.extend(_monthly("Hulu", "-15.99", 12))
    transactions.extend(_monthly("YouTube Premium", "-13.99", 15))
    transactions.append(Txn(_on(9, 18), "The New York Times", Decimal("-17.00"), "Subscriptions"))

    transactions.extend(
        _charges(
            [
                (6, 4, "DoorDash", "-80.00", "Dining"),
                (6, 6, "DoorDash", "-80.00", "Dining"),
                (6, 18, "Chipotle", "-80.00", "Dining"),
                (6, 8, "Amazon", "-70.00", "Shopping"),
                (6, 21, "Target", "-50.00", "Shopping"),
                (6, 2, "Metro Transit", "-120.00", "Transportation"),
                (6, 11, "Uber", "-60.00", "Transportation"),
                (6, 25, "Uber", "-60.00", "Transportation"),
                (6, 7, "Trader Joe's", "-170.00", "Groceries"),
                (6, 20, "Trader Joe's", "-170.00", "Groceries"),
                (7, 3, "DoorDash", "-90.00", "Dining"),
                (7, 9, "Uber Eats", "-90.00", "Dining"),
                (7, 19, "Chipotle", "-85.00", "Dining"),
                (7, 6, "Amazon", "-80.00", "Shopping"),
                (7, 22, "Target", "-65.00", "Shopping"),
                (7, 2, "Metro Transit", "-120.00", "Transportation"),
                (7, 14, "Uber", "-70.00", "Transportation"),
                (7, 27, "Uber", "-65.00", "Transportation"),
                (7, 8, "Trader Joe's", "-180.00", "Groceries"),
                (7, 21, "Trader Joe's", "-175.00", "Groceries"),
                (8, 4, "DoorDash", "-32.10", "Dining"),
                (8, 8, "Uber Eats", "-28.40", "Dining"),
                (8, 12, "Chipotle", "-41.20", "Dining"),
                (8, 15, "Sweetgreen", "-22.50", "Dining"),
                (8, 19, "DoorDash", "-36.80", "Dining"),
                (8, 22, "Thai Palace", "-45.00", "Dining"),
                (8, 26, "Uber Eats", "-38.20", "Dining"),
                (8, 28, "Chipotle", "-35.80", "Dining"),
                (8, 5, "Amazon", "-54.20", "Shopping"),
                (8, 11, "Amazon", "-38.40", "Shopping"),
                (8, 16, "Target", "-41.10", "Shopping"),
                (8, 24, "Target", "-26.30", "Shopping"),
                (8, 2, "Metro Transit", "-120.00", "Transportation"),
                (8, 9, "Uber", "-31.20", "Transportation"),
                (8, 13, "Uber", "-24.50", "Transportation"),
                (8, 18, "Uber", "-28.40", "Transportation"),
                (8, 23, "Uber", "-22.10", "Transportation"),
                (8, 29, "Uber", "-23.80", "Transportation"),
                (8, 6, "Trader Joe's", "-88.20", "Groceries"),
                (8, 10, "Trader Joe's", "-74.10", "Groceries"),
                (8, 17, "Trader Joe's", "-69.40", "Groceries"),
                (8, 23, "Trader Joe's", "-66.15", "Groceries"),
                (8, 30, "Trader Joe's", "-62.15", "Groceries"),
                (9, 2, "DoorDash", "-42.18", "Dining"),
                (9, 4, "Uber Eats", "-38.50", "Dining"),
                (9, 6, "Chipotle", "-55.20", "Dining"),
                (9, 9, "Sweetgreen", "-29.40", "Dining"),
                (9, 11, "DoorDash", "-47.80", "Dining"),
                (9, 13, "Thai Palace", "-61.10", "Dining"),
                (9, 16, "Uber Eats", "-33.25", "Dining"),
                (9, 18, "Chipotle", "-44.90", "Dining"),
                (9, 20, "DoorDash", "-52.15", "Dining"),
                (9, 22, "Sweetgreen", "-28.70", "Dining"),
                (9, 24, "Uber Eats", "-36.40", "Dining"),
                (9, 26, "Thai Palace", "-41.22", "Dining"),
                (9, 27, "DoorDash", "-50.10", "Dining"),
                (9, 28, "Chipotle", "-50.10", "Dining"),
                (9, 3, "Amazon", "-86.40", "Shopping"),
                (9, 8, "Amazon", "-64.20", "Shopping"),
                (9, 14, "Target", "-41.15", "Shopping"),
                (9, 17, "Amazon", "-29.99", "Shopping"),
                (9, 21, "Target", "-72.30", "Shopping"),
                (9, 25, "Zara", "-48.16", "Shopping"),
                (9, 29, "Zara", "-85.80", "Shopping"),
                (9, 2, "Metro Transit", "-120.00", "Transportation"),
                (9, 7, "Uber", "-28.40", "Transportation"),
                (9, 12, "Uber", "-22.15", "Transportation"),
                (9, 15, "Uber", "-31.80", "Transportation"),
                (9, 19, "Uber", "-18.65", "Transportation"),
                (9, 23, "Uber", "-24.00", "Transportation"),
                (9, 30, "Uber", "-26.00", "Transportation"),
                (9, 5, "Trader Joe's", "-92.40", "Groceries"),
                (9, 9, "Trader Joe's", "-78.15", "Groceries"),
                (9, 16, "Trader Joe's", "-64.80", "Groceries"),
                (9, 22, "Trader Joe's", "-71.25", "Groceries"),
                (9, 28, "Trader Joe's", "-73.40", "Groceries"),
                (9, 14, "Best Buy", "-340.00", "Unexpected"),
            ]
        )
    )
    return transactions
