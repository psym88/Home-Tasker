"""Pure recurrence calculations."""

import calendar
from datetime import date, timedelta
from typing import Any

from .due import task_due_date


def validate_schedule(task: dict[str, Any]) -> None:
    """Reject incomplete fixed calendar rules."""
    if task.get("schedule_type") != "fixed":
        return
    if task.get("schedule_unit") == "weekly" and not task.get("schedule_weekdays"):
        raise ValueError("select_at_least_one_weekday")
    if task.get("schedule_unit") == "monthly" and task.get("schedule_day") is None:
        raise ValueError("select_day_of_month")
    if task.get("schedule_unit") == "yearly":
        if task.get("schedule_month") is None:
            raise ValueError("select_month_of_year")
        if task.get("schedule_day") is None:
            raise ValueError("select_day_of_month")


def add_interval(value: date, schedule_interval: int, unit: str) -> date:
    """Advance a date by a simple sliding schedule_interval."""
    if unit == "day":
        return value + timedelta(days=schedule_interval)
    if unit == "week":
        return value + timedelta(weeks=schedule_interval)
    day = value.day
    if unit == "month":
        index = value.month - 1 + schedule_interval
        year, month = value.year + index // 12, index % 12 + 1
        return date(year, month, min(day, calendar.monthrange(year, month)[1]))
    if unit == "year":
        year = value.year + schedule_interval
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
    start = date.fromisoformat(task.get("schedule_start_date") or today.isoformat())
    if task["schedule_type"] == "sliding":
        return start

    schedule_unit = task.get("schedule_unit", "monthly")
    if schedule_unit == "daily":
        return start
    if schedule_unit == "weekly":
        schedule_weekdays = sorted(set(int(day) for day in task["schedule_weekdays"]))
        for offset in range(7):
            candidate = start + timedelta(days=offset)
            if candidate.weekday() in schedule_weekdays:
                return candidate
    if schedule_unit == "monthly":
        selected = task["schedule_day"]
        for offset in range(2):
            index = start.month - 1 + offset
            year, month = start.year + index // 12, index % 12 + 1
            candidate = _calendar_date(year, month, selected)
            if candidate >= start:
                return candidate
    if schedule_unit == "yearly":
        month = int(task["schedule_month"])
        selected = task["schedule_day"]
        for year in (start.year, start.year + 1):
            candidate = _calendar_date(year, month, selected)
            if candidate >= start:
                return candidate
    raise ValueError("invalid_frequency")


def next_due(task: dict[str, Any], completed: date) -> date:
    """Return the next future occurrence for a task without an end date."""
    schedule_interval = max(1, int(task.get("schedule_interval") or 1))
    schedule_unit = task.get("schedule_unit", "monthly")
    due = task_due_date(task)

    if task["schedule_type"] == "sliding":
        unit = {"daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"}[schedule_unit]
        return add_interval(completed, schedule_interval, unit)

    # Completing a calendar task early must not consume its upcoming occurrence.
    if completed < due:
        return due

    anchor = date.fromisoformat(
        task.get("schedule_anchor_date") or task_due_date(task).isoformat()
    )
    # Completing on time advances once; completing late skips missed occurrences.
    cursor = completed + timedelta(days=1)
    if schedule_unit == "daily":
        elapsed = (cursor - anchor).days
        steps = max(1, (elapsed + schedule_interval - 1) // schedule_interval)
        candidate = anchor + timedelta(days=steps * schedule_interval)
        return candidate if candidate >= cursor else candidate + timedelta(days=schedule_interval)

    if schedule_unit == "weekly":
        schedule_weekdays = sorted(set(int(day) for day in task.get("schedule_weekdays") or [anchor.weekday()]))
        anchor_week = anchor - timedelta(days=anchor.weekday())
        for offset in range(0, schedule_interval * 7 + 7):
            candidate = cursor + timedelta(days=offset)
            week = candidate - timedelta(days=candidate.weekday())
            if ((week - anchor_week).days // 7) % schedule_interval == 0 and candidate.weekday() in schedule_weekdays:
                return candidate
        raise ValueError("invalid_weekly_schedule")

    if schedule_unit == "monthly":
        selected = task.get("schedule_day") or anchor.day
        month_delta = (cursor.year - anchor.year) * 12 + cursor.month - anchor.month
        for offset in range(max(0, month_delta), max(0, month_delta) + schedule_interval + 2):
            if offset % schedule_interval:
                continue
            index = anchor.month - 1 + offset
            year, month = anchor.year + index // 12, index % 12 + 1
            candidate = _calendar_date(year, month, selected)
            if candidate >= cursor:
                return candidate
        raise ValueError("invalid_monthly_schedule")

    if schedule_unit == "yearly":
        month = int(task.get("schedule_month") or anchor.month)
        selected = task.get("schedule_day") or anchor.day
        for year in range(max(cursor.year, anchor.year), max(cursor.year, anchor.year) + schedule_interval + 2):
            if (year - anchor.year) % schedule_interval:
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
        current_task["task_due"] = due.isoformat()
        current_completion = due
    return values


def due_sequence(task: dict[str, Any], today: date, count: int = 6) -> list[date]:
    """Return an initial due date followed by consecutive occurrences."""
    if count <= 0:
        return []
    first = initial_due(task, today)
    values = [first]
    current_task = {**task, "task_due": first.isoformat(), "schedule_anchor_date": first.isoformat()}
    current_completion = first
    for _ in range(count - 1):
        due = next_due(current_task, current_completion)
        values.append(due)
        current_task["task_due"] = due.isoformat()
        current_completion = due
    return values
