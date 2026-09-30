from datetime import date
from decimal import Decimal

from app.analysis import build_autopsy, find_recurring
from app.domain import Txn
from app.explain import answer_from_summary
from app.sample_data import sample_transactions


def test_september_explains_the_increase():
    autopsy = build_autopsy(sample_transactions(), "2026-09")

    assert autopsy.income == Decimal("4100.00")
    assert autopsy.remaining == autopsy.income - autopsy.spending
    assert autopsy.spending_delta is not None and autopsy.spending_delta > 0
    assert autopsy.drivers == ["an unexpected purchase", "dining", "shopping"]
    assert "more than August" in autopsy.narrative
    assert "Netflix went up from $15.49 to $22.99" in autopsy.narrative
    assert "The New York Times showed up for the first time" in autopsy.narrative

    subscriptions = {item.merchant: item for item in autopsy.recurring}
    assert subscriptions["Spotify"].monthly_amount == Decimal("11.99")
    assert subscriptions["Spotify"].occurrences == 4
    assert subscriptions["Spotify"].total_spent == Decimal("47.96")
    assert subscriptions["Netflix"].previous_amount == Decimal("15.49")
    assert subscriptions["Netflix"].monthly_amount == Decimal("22.99")
    assert "price_increase" in subscriptions["Netflix"].flags
    assert "The New York Times" not in subscriptions
    assert "Harbor Apartments" not in subscriptions
    assert "Best Buy" not in subscriptions
    assert [item.merchant for item in autopsy.possible_new] == ["The New York Times"]


def test_june_has_no_prior_month_to_compare():
    autopsy = build_autopsy(sample_transactions(), "2026-06")
    assert autopsy.spending_delta is None
    assert autopsy.narrative.startswith("In June you brought in")
    assert "price_increase" not in {flag for item in autopsy.recurring for flag in item.flags}


def test_weekly_charges_are_not_treated_as_subscriptions():
    transactions = [
        Txn(date(2026, 9, 1), "Cafe", Decimal("-6.00"), "Subscriptions"),
        Txn(date(2026, 9, 8), "Cafe", Decimal("-6.00"), "Subscriptions"),
        Txn(date(2026, 9, 15), "Cafe", Decimal("-6.00"), "Subscriptions"),
        Txn(date(2026, 9, 22), "Cafe", Decimal("-6.00"), "Subscriptions"),
    ]
    assert find_recurring(transactions, "Subscriptions") == []


def test_cancel_question_adds_up_the_named_charges():
    autopsy = build_autopsy(sample_transactions(), "2026-09")
    answer = answer_from_summary("What happens if I cancel Spotify and Hulu?", autopsy)
    assert answer == "Canceling Spotify and Hulu would save about $27.98 a month, or $335.76 a year."


def test_subscription_question_counts_confirmed_charges():
    autopsy = build_autopsy(sample_transactions(), "2026-09")
    answer = answer_from_summary("What am I paying in subscriptions?", autopsy)
    assert "7 recurring charges" in answer
    assert "$148.93 a month" in answer
    assert "The New York Times may be new." in answer
