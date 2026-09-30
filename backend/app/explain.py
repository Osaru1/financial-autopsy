import json
import logging
import re
from decimal import Decimal

import httpx

from app.config import settings
from app.domain import Autopsy
from app.money import join_phrases, spoken

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You explain someone's finances in plain, calm language.
Use only the numbers in the financial data. Never invent amounts, merchants, or dates.
Write 2 to 4 short sentences. No bullet points and no preamble.
Talk about what happened to their money.
Do not mention tools, models, prompts, or data formats.
If they ask what canceling would save, add up the monthly amounts they named. If they did not name any, add up every confirmed subscription, and give both the monthly and yearly figure."""

GENERIC_WORDS = {"apple", "the", "new", "york", "premium", "planet"}


CANCEL_WORDS = {
    "cancel",
    "canceled",
    "cancelled",
    "canceling",
    "cancelling",
    "save",
    "saved",
    "saving",
    "drop",
    "cut",
}
SUBSCRIPTION_WORDS = {"subscription", "subscriptions", "recurring"}


def answer_from_summary(question: str, autopsy: Autopsy) -> str:
    text = question.casefold()
    tokens = set(re.findall(r"[a-z0-9']+", text))
    subscriptions = autopsy.recurring
    if tokens & CANCEL_WORDS:
        matched = [item for item in subscriptions + autopsy.possible_new if _mentioned(item.merchant, text)]
        matched.sort(key=lambda item: _mention_at(item.merchant, text))
        chosen = matched or subscriptions
        monthly = sum((item.monthly_amount for item in chosen), Decimal("0.00"))
        if matched:
            names = join_phrases([item.merchant for item in matched])
            return (
                f"Canceling {names} would save about {spoken(monthly)} a month, "
                f"or {spoken(monthly * 12)} a year."
            )
        return (
            f"Canceling every confirmed subscription would save about {spoken(monthly)} a month, "
            f"or {spoken(monthly * 12)} a year."
        )

    if tokens & SUBSCRIPTION_WORDS:
        monthly = sum((item.monthly_amount for item in subscriptions), Decimal("0.00"))
        sentence = (
            f"You have {len(subscriptions)} recurring charges, about {spoken(monthly)} a month, "
            f"or {spoken(monthly * 12)} a year."
        )
        if autopsy.possible_new:
            names = join_phrases([item.merchant for item in autopsy.possible_new])
            sentence += f" {names} may be new."
        return sentence

    return autopsy.narrative


async def explain_question(question: str, autopsy: Autopsy, context: dict) -> dict[str, str]:
    """The model only receives the summary. It does not see every transaction."""
    calculated = answer_from_summary(question, autopsy)
    if not settings.llm_api_key:
        return {"answer": calculated, "source": "calculated"}
    try:
        answer = await _complete(question, context)
    except Exception as exc:
        logger.warning("Language model request failed: %s", exc)
        return {"answer": calculated, "source": "calculated"}
    return {"answer": answer, "source": "model"}


async def _complete(question: str, context: dict) -> str:
    payload = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nFinancial data:\n{json.dumps(context)}",
            },
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
    return body["choices"][0]["message"]["content"].strip()


def _mention_at(merchant: str, question: str) -> int:
    words = [merchant.casefold(), *[word for word in merchant.casefold().split() if len(word) >= 4 and word not in GENERIC_WORDS]]
    positions = [question.find(word) for word in words if question.find(word) >= 0]
    return min(positions) if positions else 0


def _mentioned(merchant: str, question: str) -> bool:
    haystack = f" {' '.join(re.findall(r"[a-z0-9']+", question))} "
    if f" {merchant.casefold()} " in haystack:
        return True
    words = [word for word in merchant.casefold().split() if len(word) >= 4 and word not in GENERIC_WORDS]
    return any(f" {word} " in haystack for word in words)
