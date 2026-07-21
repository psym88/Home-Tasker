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
    if task.get("frequency") == "yearly":
        if task.get("month_of_year") is None:
            raise ValueError("select_month_of_year")
        if task.get("day_of_month") is None:
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
    if unit == "year":
        year = value.year + interval
        return date(year, value.month, min(day, calendar.monthrange(year, value.month)[1]))
    raise ValueError("invalid_frequency")


def _calendar_date(year: int, month: int, selected: int | str) -> date:
    """Return a selected calendar day, clamped to the month's last day."""
    last = calendar.monthrange(year, month)[1]
    day = last if selected == "last" else min(int(selected), last)
    return date(year, month, day)


def initial_due(task: dict[str, Any], today: date) -> date:
    """Calculate the first due date from a schedule and optional start boundary."""
    validate_schedule(task)
    start = date.fromisoformat(task.get("start_date") or today.isoformat())
    if task["recurrence_mode"] == "sliding":
        return start

    frequency = task.get("frequency", "monthly")
    if frequency == "daily":
        return start
    if frequency == "weekly":
        weekdays = sorted(set(int(day) for day in task["weekdays"]))
        for offset in range(7):
            candidate = start + timedelta(days=offset)
            if candidate.weekday() in weekdays:
                return candidate
    if frequency == "monthly":
        selected = task["day_of_month"]
        for offset in range(2):
            index = start.month - 1 + offset
            year, month = start.year + index // 12, index % 12 + 1
            candidate = _calendar_date(year, month, selected)
            if candidate >= start:
                return candidate
    if frequency == "yearly":
        month = int(task["month_of_year"])
        selected = task["day_of_month"]
        for year in (start.year, start.year + 1):
            candidate = _calendar_date(year, month, selected)
            if candidate >= start:
                return candidate
    raise ValueError("invalid_frequency")


def next_due(task: dict[str, Any], completed: date) -> date:
    """Return the next future occurrence for a task without an end date."""
    interval = max(1, int(task.get("interval") or 1))
    frequency = task.get("frequency", "monthly")
    due = date.fromisoformat(task["due_date"])

    if task["recurrence_mode"] == "sliding":
        unit = {"daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"}[frequency]
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
            candidate = _calendar_date(year, month, selected)
            if candidate >= cursor:
                return candidate
        raise ValueError("invalid_monthly_schedule")

    if frequency == "yearly":
        month = int(task.get("month_of_year") or anchor.month)
        selected = task.get("day_of_month") or anchor.day
        for year in range(max(cursor.year, anchor.year), max(cursor.year, anchor.year) + interval + 2):
            if (year - anchor.year) % interval:
                continue
            candidate = _calendar_date(year, month, selected)
            if candidate >= cursor:
                return candidate
        raise ValueError("invalid_yearly_schedule")

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


def due_sequence(task: dict[str, Any], today: date, count: int = 6) -> list[date]:
    """Return an initial due date followed by consecutive occurrences."""
    if count <= 0:
        return []
    first = initial_due(task, today)
    values = [first]
    current_task = {**task, "due_date": first.isoformat(), "schedule_anchor": first.isoformat()}
    current_completion = first
    for _ in range(count - 1):
        due = next_due(current_task, current_completion)
        values.append(due)
        current_task["due_date"] = due.isoformat()
        current_completion = due
    return values
