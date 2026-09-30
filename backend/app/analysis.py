from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.calendar import month_end, month_key, month_label, month_name, previous_month
from app.domain import Autopsy, CategoryTotal, LargeTransaction, RecurringItem, Txn
from app.money import join_phrases, spoken

DRIVER_LABELS = {
    "Unexpected": "an unexpected purchase",
    "Dining": "dining",
    "Shopping": "shopping",
    "Subscriptions": "subscriptions",
    "Transportation": "transportation",
    "Groceries": "groceries",
    "Rent": "rent",
}
SUBSCRIPTION_CATEGORY = "Subscriptions"
LARGE_TRANSACTION = Decimal("200")


def available_months(transactions: list[Txn]) -> list[str]:
    return sorted({month_key(txn.posted_on) for txn in transactions}, reverse=True)


def build_autopsy(transactions: list[Txn], month: str) -> Autopsy:
    history = [txn for txn in transactions if txn.posted_on <= month_end(month)]
    current = [txn for txn in history if month_key(txn.posted_on) == month]
    income = _sum_income(current)
    categories = _category_totals(current)
    spending = sum((item.amount for item in categories), Decimal("0.00"))
    previous = previous_month(month)
    previous_totals = None
    if any(month_key(txn.posted_on) == previous for txn in history):
        previous_totals = {item.category: item.amount for item in _category_totals(
            [txn for txn in history if month_key(txn.posted_on) == previous]
        )}

    compared: list[CategoryTotal] = []
    for item in categories:
        delta = None if previous_totals is None else item.amount - previous_totals.get(item.category, Decimal("0.00"))
        compared.append(CategoryTotal(item.category, item.amount, delta))
    if previous_totals is not None:
        for category, amount in previous_totals.items():
            if not any(item.category == category for item in compared):
                compared.append(CategoryTotal(category, Decimal("0.00"), Decimal("0.00") - amount))
    compared.sort(key=lambda item: item.amount, reverse=True)

    spending_delta = None
    previous_label = None
    drivers: list[str] = []
    if previous_totals is not None:
        previous_spending = sum(previous_totals.values(), Decimal("0.00"))
        spending_delta = spending - previous_spending
        previous_label = month_name(previous)
        increases = [item for item in compared if item.delta is not None and item.delta > 0]
        increases.sort(key=lambda item: item.delta or Decimal("0"), reverse=True)
        drivers = [DRIVER_LABELS.get(item.category, item.category.lower()) for item in increases[:3]]

    recurring = _mark_new(find_recurring(history, SUBSCRIPTION_CATEGORY), month_end(month))
    possible_new = find_possible_new(history, month)
    narrative = write_narrative(
        income=income,
        spending=spending,
        remaining=income - spending,
        month_name_text=month_name(month),
        previous_label=previous_label,
        spending_delta=spending_delta,
        drivers=drivers,
        recurring=recurring,
        possible_new=possible_new,
    )
    return Autopsy(
        month=month,
        month_label=month_label(month),
        income=income,
        spending=spending,
        remaining=income - spending,
        categories=compared,
        previous_month=previous if previous_totals is not None else None,
        previous_label=previous_label,
        spending_delta=spending_delta,
        drivers=drivers,
        narrative=narrative,
        recurring=recurring,
        possible_new=possible_new,
        large_transactions=large_transactions(current),
    )


def find_recurring(transactions: list[Txn], category: str | None = None) -> list[RecurringItem]:
    groups: dict[str, list[Txn]] = defaultdict(list)
    for txn in transactions:
        if txn.amount >= 0:
            continue
        if category is not None and txn.category != category:
            continue
        groups[_merchant_key(txn.merchant)].append(txn)

    items: list[RecurringItem] = []
    for group in groups.values():
        ordered = sorted(group, key=lambda txn: txn.posted_on)
        if len(ordered) < 2:
            continue
        gaps = [(later.posted_on - earlier.posted_on).days for earlier, later in zip(ordered, ordered[1:])]
        if not all(20 <= gap <= 40 for gap in gaps):
            continue
        amounts = [abs(txn.amount) for txn in ordered]
        if max(amounts) > min(amounts) * Decimal("2"):
            continue
        latest = amounts[-1]
        prior = amounts[-2]
        flags: list[str] = []
        previous_amount = None
        if latest > prior * Decimal("1.02"):
            flags.append("price_increase")
            previous_amount = prior
        items.append(
            RecurringItem(
                merchant=ordered[-1].merchant,
                category=ordered[-1].category,
                monthly_amount=latest,
                annual_amount=latest * 12,
                first_seen=ordered[0].posted_on,
                last_seen=ordered[-1].posted_on,
                occurrences=len(ordered),
                total_spent=sum(amounts, Decimal("0.00")),
                previous_amount=previous_amount,
                flags=tuple(flags),
            )
        )
    items.sort(key=lambda item: item.monthly_amount, reverse=True)
    return items


def find_possible_new(transactions: list[Txn], month: str) -> list[RecurringItem]:
    year, month_number = (int(month[:4]), int(month[5:]))
    month_start = date(year, month_number, 1)
    if not any(txn.posted_on < month_start for txn in transactions):
        return []

    in_month: dict[str, list[Txn]] = defaultdict(list)
    seen_earlier: set[str] = set()
    for txn in transactions:
        if txn.amount >= 0 or txn.category != SUBSCRIPTION_CATEGORY:
            continue
        key = _merchant_key(txn.merchant)
        posted = (txn.posted_on.year, txn.posted_on.month)
        if posted == (year, month_number):
            in_month[key].append(txn)
        elif posted < (year, month_number):
            seen_earlier.add(key)

    items: list[RecurringItem] = []
    for key, group in in_month.items():
        if key in seen_earlier or len(group) != 1:
            continue
        txn = group[0]
        amount = abs(txn.amount)
        items.append(
            RecurringItem(
                merchant=txn.merchant,
                category=txn.category,
                monthly_amount=amount,
                annual_amount=amount * 12,
                first_seen=txn.posted_on,
                last_seen=txn.posted_on,
                occurrences=1,
                total_spent=amount,
                previous_amount=None,
                flags=("possible_new",),
            )
        )
    items.sort(key=lambda item: item.monthly_amount, reverse=True)
    return items


def large_transactions(transactions: list[Txn]) -> list[LargeTransaction]:
    charges = [txn for txn in transactions if txn.amount <= -LARGE_TRANSACTION]
    charges.sort(key=lambda txn: txn.amount)
    return [
        LargeTransaction(txn.posted_on, txn.merchant, abs(txn.amount), txn.category)
        for txn in charges[:5]
    ]


def write_narrative(
    *,
    income: Decimal,
    spending: Decimal,
    remaining: Decimal,
    month_name_text: str,
    previous_label: str | None,
    spending_delta: Decimal | None,
    drivers: list[str],
    recurring: list[RecurringItem],
    possible_new: list[RecurringItem],
) -> str:
    if previous_label is None or spending_delta is None:
        sentence = (
            f"In {month_name_text} you brought in {spoken(income)} and spent {spoken(spending)}, "
            f"leaving {spoken(remaining)}."
        )
    elif spending_delta > 0:
        sentence = f"You spent {spoken(spending_delta)} more than {previous_label}."
        if drivers:
            sentence += f" Most of the increase came from {join_phrases(drivers)}."
    elif spending_delta < 0:
        sentence = f"You spent {spoken(abs(spending_delta))} less than {previous_label}."
    else:
        sentence = f"Spending was about the same as {previous_label}."

    notes: list[str] = []
    increases = [item for item in recurring if "price_increase" in item.flags and item.previous_amount is not None]
    if increases:
        changes = [
            f"{item.merchant} went up from {spoken(item.previous_amount)} to {spoken(item.monthly_amount)}"
            for item in increases
            if item.previous_amount is not None
        ]
        notes.append(f"{join_phrases(changes)}.")
    if possible_new:
        arrivals = [
            f"{item.merchant} showed up for the first time, at {spoken(item.monthly_amount)}"
            for item in possible_new
        ]
        notes.append(f"{join_phrases(arrivals)}.")
    if notes:
        return f"{sentence} {' '.join(notes)}"
    return sentence


def _mark_new(items: list[RecurringItem], as_of: date) -> list[RecurringItem]:
    marked: list[RecurringItem] = []
    for item in items:
        if (as_of - item.first_seen).days <= 45 and "new" not in item.flags:
            marked.append(_replace_flags(item, item.flags + ("new",)))
        else:
            marked.append(item)
    return marked


def _replace_flags(item: RecurringItem, flags: tuple[str, ...]) -> RecurringItem:
    return RecurringItem(
        merchant=item.merchant,
        category=item.category,
        monthly_amount=item.monthly_amount,
        annual_amount=item.annual_amount,
        first_seen=item.first_seen,
        last_seen=item.last_seen,
        occurrences=item.occurrences,
        total_spent=item.total_spent,
        previous_amount=item.previous_amount,
        flags=flags,
    )


def _category_totals(transactions: list[Txn]) -> list[CategoryTotal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for txn in transactions:
        if txn.amount < 0:
            totals[txn.category] += abs(txn.amount)
    return [CategoryTotal(category, amount, None) for category, amount in totals.items()]


def _sum_income(transactions: list[Txn]) -> Decimal:
    return sum((txn.amount for txn in transactions if txn.amount > 0), Decimal("0.00"))


def _merchant_key(merchant: str) -> str:
    return " ".join(merchant.casefold().split())
