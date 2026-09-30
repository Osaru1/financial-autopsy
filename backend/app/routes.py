import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.analysis import available_months, build_autopsy
from app.calendar import parse_month
from app.database import get_db
from app.domain import Txn
from app.explain import explain_question
from app.models import Transaction
from app.sample_data import sample_transactions
from app.serialize import autopsy_payload, empty_payload

router = APIRouter(prefix="/api")


class AskRequest(BaseModel):
    question: str
    month: str | None = None

    @field_validator("question")
    @classmethod
    def question_present(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Ask a question about your money")
        if len(cleaned) > 500:
            raise ValueError("Keep the question under 500 characters")
        return cleaned


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, bool]:
    db.execute(text("SELECT 1"))
    return {"ok": True}


@router.get("/autopsy")
def get_autopsy(
    month: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    transactions = _load(db)
    if not transactions:
        return empty_payload()
    selected = _select_month(transactions, month)
    return autopsy_payload(build_autopsy(transactions, selected), available_months(transactions))


@router.get("/transactions")
def get_transactions(
    month: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    transactions = _load(db)
    if month is not None:
        _validate_month(month)
        transactions = [txn for txn in transactions if txn.posted_on.isoformat().startswith(month)]
    return {
        "transactions": [
            {
                "posted_on": txn.posted_on.isoformat(),
                "merchant": txn.merchant,
                "amount": f"{txn.amount.quantize(Decimal('0.01'))}",
                "category": txn.category,
            }
            for txn in transactions
        ]
    }


@router.post("/transactions/seed")
def seed_transactions(db: Session = Depends(get_db)) -> dict:
    saved = _replace(db, sample_transactions())
    selected = available_months(saved)[0]
    return autopsy_payload(build_autopsy(saved, selected), available_months(saved))


@router.post("/transactions/import")
async def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
        parsed = _parse_csv(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.add_all(_rows(parsed))
    db.commit()
    return {"imported": len(parsed)}


@router.post("/ask")
async def ask(body: AskRequest, db: Session = Depends(get_db)) -> dict:
    transactions = _load(db)
    if not transactions:
        raise HTTPException(status_code=400, detail="Load some transactions before asking a question.")
    selected = _select_month(transactions, body.month)
    autopsy = build_autopsy(transactions, selected)
    payload = autopsy_payload(autopsy, available_months(transactions))
    answer = await explain_question(body.question, autopsy, payload)
    return {"month": selected, **answer}


def _load(db: Session) -> list[Txn]:
    rows = db.scalars(select(Transaction).order_by(Transaction.posted_on, Transaction.id)).all()
    return [
        Txn(
            posted_on=row.posted_on,
            merchant=row.merchant,
            amount=Decimal(row.amount),
            category=row.category,
        )
        for row in rows
    ]


def _replace(db: Session, transactions: list[Txn]) -> list[Txn]:
    db.execute(delete(Transaction))
    db.add_all(_rows(transactions))
    db.commit()
    return transactions


def _rows(transactions: list[Txn]) -> list[Transaction]:
    return [
        Transaction(
            posted_on=txn.posted_on,
            merchant=txn.merchant,
            amount=txn.amount,
            category=txn.category,
        )
        for txn in transactions
    ]


def _select_month(transactions: list[Txn], month: str | None) -> str:
    months = available_months(transactions)
    if month is None:
        return months[0]
    _validate_month(month)
    if month not in months:
        raise HTTPException(status_code=404, detail=f"No transactions in {month}.")
    return month


def _validate_month(month: str) -> None:
    try:
        parse_month(month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _parse_csv(text: str) -> list[Txn]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("The CSV needs a header row.")
    header = {name.strip().casefold(): name for name in reader.fieldnames if name}
    missing = {"date", "merchant", "amount", "category"} - set(header)
    if missing:
        raise ValueError("The CSV needs date, merchant, amount, and category columns.")

    transactions: list[Txn] = []
    for index, row in enumerate(reader, start=2):
        try:
            posted = row[header["date"]].strip()
            year, month, day = (int(part) for part in posted.split("-"))
            posted_on = date(year, month, day)
            merchant = row[header["merchant"]].strip()
            amount = Decimal(row[header["amount"]].strip())
            category = row[header["category"]].strip() or "Uncategorized"
        except (InvalidOperation, TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"Row {index} could not be read. Use dates like 2026-09-01.") from exc
        if not merchant:
            raise ValueError(f"Row {index} is missing a merchant.")
        transactions.append(Txn(posted_on, merchant, amount, category))
    if not transactions:
        raise ValueError("The CSV has no transactions.")
    return transactions
