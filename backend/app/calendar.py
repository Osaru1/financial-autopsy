from datetime import date, timedelta


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def parse_month(value: str) -> tuple[int, int]:
    parts = value.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise ValueError("Month must look like 2026-09")
    try:
        year, month = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError("Month must look like 2026-09") from exc
    if not 1 <= month <= 12:
        raise ValueError("Month must look like 2026-09")
    return year, month


def month_end(value: str) -> date:
    year, month = parse_month(value)
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def previous_month(value: str) -> str:
    year, month = parse_month(value)
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


def month_name(value: str) -> str:
    year, month = parse_month(value)
    return date(year, month, 1).strftime("%B")


def month_label(value: str) -> str:
    year, month = parse_month(value)
    return date(year, month, 1).strftime("%B %Y")
