from decimal import Decimal


def money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def spoken(value: Decimal) -> str:
    amount = abs(value.quantize(Decimal("0.01")))
    if amount == amount.to_integral_value():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"


def join_phrases(phrases: list[str]) -> str:
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"
    return ", ".join(phrases[:-1]) + f", and {phrases[-1]}"
