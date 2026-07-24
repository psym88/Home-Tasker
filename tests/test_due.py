"""Tests for native task due values and due events."""

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from custom_components.home_tasker.due import (
    TaskDueEventScheduler,
    parse_task_due,
    task_due_with_date,
)


def test_task_due_accepts_dates_and_datetimes():
    assert parse_task_due("2026-07-25") == date(2026, 7, 25)
    assert parse_task_due("2026-07-25T08:00:00+02:00") == datetime(
        2026, 7, 25, 8, tzinfo=timezone(timedelta(hours=2))
    )


def test_recurrence_preserves_due_time():
    task = {"task_due": "2026-07-25T08:00:00+02:00"}

    assert task_due_with_date(task, date(2026, 8, 25)) == (
        "2026-08-25T08:00:00+02:00"
    )


def test_due_scheduler_fires_one_event_per_task(monkeypatch):
    events = []
    hass = SimpleNamespace(
        bus=SimpleNamespace(
            async_fire=lambda event_type, data, context=None: events.append(
                (event_type, data)
            )
        )
    )
    store = SimpleNamespace(
        tasks=[
            {
                "task_id": "one",
                "task_name": "One",
                "task_due": "2026-07-25T08:00:00+00:00",
            },
            {
                "task_id": "two",
                "task_name": "Two",
                "task_due": "2026-07-25T08:00:00+00:00",
            },
            {
                "task_id": "later",
                "task_name": "Later",
                "task_due": "2026-07-25T09:00:00+00:00",
            },
        ]
    )
    scheduler = TaskDueEventScheduler(hass, store)
    monkeypatch.setattr(scheduler, "reschedule", lambda: None)

    scheduler._fire_due(
        datetime(2026, 7, 25, 8, tzinfo=timezone.utc),
        datetime(2026, 7, 25, 8, 0, 1, tzinfo=timezone.utc),
    )

    assert [data["resource_id"] for _, data in events] == ["one", "two"]
    assert all(data["action"] == "task_due" for _, data in events)
