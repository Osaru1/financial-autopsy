from decimal import Decimal

from app.domain import Autopsy, LargeTransaction, RecurringItem
from app.money import money


def autopsy_payload(autopsy: Autopsy, available: list[str]) -> dict:
    monthly = sum((item.monthly_amount for item in autopsy.recurring), Decimal("0.00"))
    return {
        "empty": False,
        "month": autopsy.month,
        "month_label": autopsy.month_label,
        "available_months": available,
        "income": money(autopsy.income),
        "spending": money(autopsy.spending),
        "remaining": money(autopsy.remaining),
        "previous_month": autopsy.previous_month,
        "previous_label": autopsy.previous_label,
        "spending_delta": None if autopsy.spending_delta is None else money(autopsy.spending_delta),
        "drivers": autopsy.drivers,
        "narrative": autopsy.narrative,
        "categories": [
            {
                "category": item.category,
                "amount": money(item.amount),
                "delta": None if item.delta is None else money(item.delta),
            }
            for item in autopsy.categories
            if item.amount > 0
        ],
        "subscriptions": {
            "count": len(autopsy.recurring),
            "monthly_cost": money(monthly),
            "annual_cost": money(monthly * 12),
            "items": [_subscription(item) for item in autopsy.recurring],
            "possible_new": [_subscription(item) for item in autopsy.possible_new],
        },
        "large_transactions": [_large(item) for item in autopsy.large_transactions],
    }


def empty_payload() -> dict:
    return {"empty": True, "available_months": []}


def _subscription(item: RecurringItem) -> dict:
    return {
        "merchant": item.merchant,
        "monthly_amount": money(item.monthly_amount),
        "annual_amount": money(item.annual_amount),
        "first_seen": item.first_seen.isoformat(),
        "last_seen": item.last_seen.isoformat(),
        "occurrences": item.occurrences,
        "total_spent": money(item.total_spent),
        "previous_amount": None if item.previous_amount is None else money(item.previous_amount),
        "flags": list(item.flags),
    }


def _large(item: LargeTransaction) -> dict:
    return {
        "posted_on": item.posted_on.isoformat(),
        "merchant": item.merchant,
        "amount": money(item.amount),
        "category": item.category,
    }
