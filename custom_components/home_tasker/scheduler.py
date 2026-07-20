"""Pure recurrence calculations."""

import calendar
from datetime import date, timedelta


def add_interval(value: date, interval: int, unit: str, anchor_day: int | None = None) -> date:
    """Advance a date while preserving monthly/yearly calendar anchors."""
    if unit == "day":
        return value + timedelta(days=interval)
    if unit == "week":
        return value + timedelta(weeks=interval)
    day = anchor_day or value.day
    if unit == "month":
        index = value.month - 1 + interval
        year, month = value.year + index // 12, index % 12 + 1
        return date(year, month, min(day, calendar.monthrange(year, month)[1]))
    if unit == "year":
        year = value.year + interval
        return date(year, value.month, min(day, calendar.monthrange(year, value.month)[1]))
    raise ValueError("invalid_interval_unit")

