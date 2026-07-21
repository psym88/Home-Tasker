"""Pure recurrence calculations."""

import calendar
from datetime import date, timedelta
from typing import Any


def validate_schedule(task: dict[str, Any]) -> None:
    """Reject incomplete fixed calendar rules."""
    if task.get("recurrence_mode") != "fixed":
        return
    if task.get("frequency") == "weekly" and not task.get("weekdays"):
        raise ValueError("select_at_least_one_weekday")
    if task.get("frequency") == "monthly" and task.get("day_of_month") is None:
        raise ValueError("select_day_of_month")


def add_interval(value: date, interval: int, unit: str, anchor_day: int | None = None) -> date:
    """Advance a date by a simple sliding interval."""
    if unit == "day":
        return value + timedelta(days=interval)
    if unit == "week":
        return value + timedelta(weeks=interval)
    day = anchor_day or value.day
    if unit == "month":
        index = value.month - 1 + interval
        year, month = value.year + index // 12, index % 12 + 1
        return date(year, month, min(day, calendar.monthrange(year, month)[1]))
    raise ValueError("invalid_frequency")


def next_due(task: dict[str, Any], completed: date) -> date:
    """Return the next future occurrence for a task without an end date."""
    interval = max(1, int(task.get("interval") or 1))
    frequency = task.get("frequency", "monthly")
    due = date.fromisoformat(task["due_date"])

    if task["recurrence_mode"] == "sliding":
        unit = {"daily": "day", "weekly": "week", "monthly": "month"}[frequency]
        return add_interval(completed, interval, unit)

    anchor = date.fromisoformat(task.get("schedule_anchor") or task["due_date"])
    # Completing early still consumes the currently scheduled occurrence;
    # completing late skips missed fixed occurrences and selects a future one.
    cursor = max(completed, due) + timedelta(days=1)
    if frequency == "daily":
        elapsed = (cursor - anchor).days
        steps = max(1, (elapsed + interval - 1) // interval)
        candidate = anchor + timedelta(days=steps * interval)
        return candidate if candidate >= cursor else candidate + timedelta(days=interval)

    if frequency == "weekly":
        weekdays = sorted(set(int(day) for day in task.get("weekdays") or [anchor.weekday()]))
        anchor_week = anchor - timedelta(days=anchor.weekday())
        for offset in range(0, interval * 7 + 7):
            candidate = cursor + timedelta(days=offset)
            week = candidate - timedelta(days=candidate.weekday())
            if ((week - anchor_week).days // 7) % interval == 0 and candidate.weekday() in weekdays:
                return candidate
        raise ValueError("invalid_weekly_schedule")

    if frequency == "monthly":
        selected = task.get("day_of_month") or anchor.day
        month_delta = (cursor.year - anchor.year) * 12 + cursor.month - anchor.month
        for offset in range(max(0, month_delta), max(0, month_delta) + interval + 2):
            if offset % interval:
                continue
            index = anchor.month - 1 + offset
            year, month = anchor.year + index // 12, index % 12 + 1
            last = calendar.monthrange(year, month)[1]
            day = last if selected == "last" else min(int(selected), last)
            candidate = date(year, month, day)
            if candidate >= cursor:
                return candidate
        raise ValueError("invalid_monthly_schedule")

    raise ValueError("invalid_frequency")


def next_due_sequence(
    task: dict[str, Any], completed: date, count: int = 2
) -> list[date]:
    """Return consecutive future occurrences using the authoritative rules."""
    values: list[date] = []
    current_task = dict(task)
    current_completion = completed
    for _ in range(max(0, count)):
        due = next_due(current_task, current_completion)
        values.append(due)
        current_task["due_date"] = due.isoformat()
        current_completion = due
    return values
