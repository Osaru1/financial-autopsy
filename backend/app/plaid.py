import asyncio
from datetime import date
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.analysis import available_months, build_autopsy
from app.config import settings
from app.database import get_db
from app.domain import Txn
from app.models import PlaidItem, Transaction
from app.serialize import autopsy_payload

router = APIRouter(prefix="/api/plaid")

PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "production": "https://production.plaid.com",
}

MISSING_KEYS = "Add PLAID_CLIENT_ID and PLAID_SECRET from the Plaid sandbox to backend/.env."


def missing_plaid_keys() -> str | None:
    if settings.plaid_client_id and settings.plaid_secret:
        return None
    return MISSING_KEYS


@router.post("/link-token")
async def create_link_token() -> dict[str, str]:
    """Ask Plaid for a link_token.

    The browser uses that token to open Plaid's bank login. The Plaid secret stays on this server.
    """
    missing = missing_plaid_keys()
    if missing:
        raise HTTPException(status_code=400, detail=missing)

    host = PLAID_HOSTS.get(settings.plaid_env)
    if host is None:
        raise HTTPException(status_code=400, detail="PLAID_ENV must be sandbox or production.")

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{host}/link/token/create",
            json={
                "client_id": settings.plaid_client_id,
                "secret": settings.plaid_secret,
                "client_name": "Financial Autopsy",
                "language": "en",
                "country_codes": ["US"],
                "user": {"client_user_id": "local-dev"},
                "products": ["transactions"],
            },
        )
    body = response.json()
    if response.status_code >= 400:
        message = body.get("error_message") or "Plaid rejected the link token request."
        raise HTTPException(status_code=502, detail=message)
    return {"link_token": body["link_token"]}


class ExchangeRequest(BaseModel):
    public_token: str


@router.post("/exchange")
async def exchange_public_token(body: ExchangeRequest, db: Session = Depends(get_db)) -> dict:
    """Trade Plaid's one-time public token for transactions.

    The access token stays in the database. The browser only receives the autopsy.
    """
    missing = missing_plaid_keys()
    if missing:
        raise HTTPException(status_code=400, detail=missing)
    if not body.public_token.strip():
        raise HTTPException(status_code=400, detail="Plaid did not return a login receipt.")

    async with httpx.AsyncClient(timeout=30) as client:
        exchanged = await _plaid(client, "/item/public_token/exchange", {"public_token": body.public_token.strip()})
        added, cursor = await _sync_transactions(client, exchanged["access_token"])

    transactions = [txn for raw in added if (txn := to_transaction(raw)) is not None]
    if not transactions:
        raise HTTPException(
            status_code=409,
            detail="Your bank connected, but the transactions were not ready yet. Try signing in again.",
        )

    _store(db, exchanged["item_id"], exchanged["access_token"], cursor, transactions)
    month = available_months(transactions)[0]
    return autopsy_payload(build_autopsy(transactions, month), available_months(transactions))


def to_transaction(raw: dict) -> Txn | None:
    if raw.get("pending"):
        return None
    posted = raw.get("date")
    if not posted:
        return None
    year, month, day = (int(part) for part in posted.split("-"))
    merchant = (raw.get("merchant_name") or raw.get("name") or "Unknown").strip()[:200]
    return Txn(
        posted_on=date(year, month, day),
        merchant=merchant or "Unknown",
        amount=our_amount(raw.get("amount", 0)),
        category=category_label(raw),
    )


def our_amount(plaid_amount: float | int | str) -> Decimal:
    """Plaid uses positive numbers for money leaving the account. This app uses negative."""
    return (-Decimal(str(plaid_amount))).quantize(Decimal("0.01"))


def category_label(raw: dict) -> str:
    primary = (raw.get("personal_finance_category") or {}).get("primary")
    if primary:
        return primary.replace("_", " ").title()[:80]
    categories = raw.get("category") or []
    if categories:
        return str(categories[0])[:80]
    return "Uncategorized"


async def _sync_transactions(client: httpx.AsyncClient, access_token: str) -> tuple[list[dict], str]:
    added: list[dict] = []
    cursor = ""
    empty_tries = 0
    for _ in range(20):
        page = await _plaid(
            client,
            "/transactions/sync",
            {"access_token": access_token, "cursor": cursor},
            allow_not_ready=True,
        )
        if page is None:
            await asyncio.sleep(1.5)
            continue
        added.extend(page.get("added") or [])
        cursor = page.get("next_cursor") or cursor
        if page.get("has_more"):
            continue
        if added or empty_tries >= 3:
            return added, cursor
        empty_tries += 1
        await asyncio.sleep(1.5)
    return added, cursor


async def _plaid(
    client: httpx.AsyncClient,
    path: str,
    payload: dict,
    allow_not_ready: bool = False,
) -> dict | None:
    host = PLAID_HOSTS.get(settings.plaid_env)
    if host is None:
        raise HTTPException(status_code=400, detail="PLAID_ENV must be sandbox or production.")
    response = await client.post(
        f"{host}{path}",
        json={
            "client_id": settings.plaid_client_id,
            "secret": settings.plaid_secret,
            **payload,
        },
    )
    body = response.json()
    if response.status_code >= 400:
        if allow_not_ready and body.get("error_code") == "PRODUCT_NOT_READY":
            return None
        message = body.get("error_message") or "Plaid could not finish that request."
        raise HTTPException(status_code=502, detail=message)
    return body


def _store(db: Session, item_id: str, access_token: str, cursor: str, transactions: list[Txn]) -> None:
    db.execute(delete(Transaction))
    db.execute(delete(PlaidItem))
    db.add(PlaidItem(item_id=item_id, access_token=access_token, cursor=cursor))
    db.add_all(
        Transaction(
            posted_on=txn.posted_on,
            merchant=txn.merchant,
            amount=txn.amount,
            category=txn.category,
        )
        for txn in transactions
    )
    db.commit()
