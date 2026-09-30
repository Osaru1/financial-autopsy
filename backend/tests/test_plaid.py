from decimal import Decimal

from app.config import settings
from app.plaid import category_label, missing_plaid_keys, our_amount, to_transaction


def test_link_token_requires_sandbox_keys(monkeypatch):
    monkeypatch.setattr(settings, "plaid_client_id", "")
    monkeypatch.setattr(settings, "plaid_secret", "")
    message = missing_plaid_keys()
    assert message is not None
    assert "PLAID_CLIENT_ID" in message


def test_link_token_is_ready_when_both_keys_exist(monkeypatch):
    monkeypatch.setattr(settings, "plaid_client_id", "sandbox-id")
    monkeypatch.setattr(settings, "plaid_secret", "sandbox-secret")
    assert missing_plaid_keys() is None


def test_plaid_spending_is_stored_as_money_leaving():
    assert our_amount(12.5) == Decimal("-12.50")
    assert our_amount(-2000) == Decimal("2000.00")


def test_plaid_transaction_becomes_one_of_ours():
    txn = to_transaction(
        {
            "amount": 11.99,
            "date": "2026-09-03",
            "merchant_name": "Spotify",
            "pending": False,
            "personal_finance_category": {"primary": "ENTERTAINMENT"},
        }
    )
    assert txn is not None
    assert txn.merchant == "Spotify"
    assert txn.amount == Decimal("-11.99")
    assert txn.category == "Entertainment"
    assert category_label({}) == "Uncategorized"
    assert to_transaction({"amount": 4, "date": "2026-09-03", "pending": True, "name": "Coffee"}) is None
