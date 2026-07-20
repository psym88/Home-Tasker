"""Scheduler unit tests."""

from datetime import date

from custom_components.home_tasker.scheduler import add_interval, next_due


def task(**values):
    return {"due_date": "2026-07-20", "schedule_anchor": "2026-07-20", "recurrence_mode": "fixed", "frequency": "daily", "interval": 1, **values}


def test_sliding_intervals():
    assert add_interval(date(2026, 7, 20), 2, "day") == date(2026, 7, 22)
    assert next_due(task(recurrence_mode="sliding", frequency="weekly", interval=2), date(2026, 7, 21)) == date(2026, 8, 4)


def test_fixed_daily_skips_overdue_occurrences():
    assert next_due(task(interval=3), date(2026, 7, 27)) == date(2026, 7, 29)
    assert next_due(task(interval=3), date(2026, 7, 18)) == date(2026, 7, 23)


def test_fixed_weekdays():
    value = task(frequency="weekly", weekdays=[0, 2, 4], interval=1)
    assert next_due(value, date(2026, 7, 20)) == date(2026, 7, 22)
    assert next_due(value, date(2026, 7, 24)) == date(2026, 7, 27)


def test_every_other_week():
    value = task(frequency="weekly", weekdays=[0], interval=2)
    assert next_due(value, date(2026, 7, 20)) == date(2026, 8, 3)


def test_month_anchor_and_last_day():
    value = task(due_date="2026-01-31", schedule_anchor="2026-01-31", frequency="monthly", day_of_month=31)
    assert next_due(value, date(2026, 1, 31)) == date(2026, 2, 28)
    value["due_date"] = "2026-02-28"
    assert next_due(value, date(2026, 2, 28)) == date(2026, 3, 31)
    value["day_of_month"] = "last"
    value["due_date"] = "2026-03-31"
    assert next_due(value, date(2026, 3, 31)) == date(2026, 4, 30)
