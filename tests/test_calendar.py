"""Home Tasker calendar tests."""

import ast
import asyncio
from datetime import date, datetime, timezone
from pathlib import Path

from custom_components.home_tasker.calendar import HomeTaskerCalendar


class FakeStore:
    tasks = [
        {
            "task_id": "task-later",
            "task_name": "Wipe shelves",
            "task_description": "Use a damp cloth",
            "task_due": "2026-07-24",
            "schedule_anchor_date": "2026-07-24",
            "schedule_type": "fixed",
            "schedule_unit": "yearly",
            "schedule_interval": 1,
            "schedule_month": 7,
            "schedule_day": 24,
        },
        {
            "task_id": "task-first-b",
            "task_name": "Clean sink",
            "task_description": None,
            "task_due": "2026-07-22",
            "schedule_anchor_date": "2026-07-22",
            "schedule_type": "fixed",
            "schedule_unit": "yearly",
            "schedule_interval": 1,
            "schedule_month": 7,
            "schedule_day": 22,
        },
        {
            "task_id": "task-first-a",
            "task_name": "Clean counter",
            "task_description": None,
            "task_due": "2026-07-22",
            "schedule_anchor_date": "2026-07-22",
            "schedule_type": "fixed",
            "schedule_unit": "yearly",
            "schedule_interval": 1,
            "schedule_month": 7,
            "schedule_day": 22,
        },
    ]


def test_calendar_uses_shared_device():
    calendar = HomeTaskerCalendar(FakeStore())

    assert calendar.device_info["name"] == "Home Tasker"
    assert calendar.unique_id == "calendar"
    assert calendar.name is None
    assert calendar.has_entity_name
    assert calendar.device_info["identifiers"] == {("home_tasker", "home_tasker")}


def test_calendar_returns_sorted_all_day_events_with_task_details():
    calendar = HomeTaskerCalendar(FakeStore())
    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 22, tzinfo=timezone.utc),
            datetime(2026, 7, 25, tzinfo=timezone.utc),
        )
    )

    assert [event.summary for event in events] == [
        "Clean counter",
        "Clean sink",
        "Wipe shelves",
    ]
    assert events[0].start == date(2026, 7, 22)
    assert events[0].end == date(2026, 7, 23)
    assert events[0].location is None
    assert events[0].uid == "task-first-a:2026-07-22"
    assert events[0].recurrence_id is None
    assert events[2].description == "Use a damp cloth"


def test_calendar_event_keeps_today_all_day_task_current(monkeypatch):
    monkeypatch.setattr(
        "custom_components.home_tasker.calendar.dt_util.utcnow",
        lambda: datetime(2026, 7, 24, 12, tzinfo=timezone.utc),
    )
    calendar = HomeTaskerCalendar(FakeStore())

    assert calendar.event is not None
    assert calendar.event.summary == "Wipe shelves"


def test_calendar_range_uses_exclusive_event_boundaries():
    calendar = HomeTaskerCalendar(FakeStore())
    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 23, tzinfo=timezone.utc),
            datetime(2026, 7, 24, tzinfo=timezone.utc),
        )
    )

    assert events == []


def test_native_platforms_are_forwarded():
    from custom_components.home_tasker.const import PLATFORMS

    assert PLATFORMS == ["calendar", "sensor", "todo"]


def test_calendar_bus_update_is_an_event_loop_callback():
    source = Path("custom_components/home_tasker/calendar.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calendar_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HomeTaskerCalendar"
    )
    handler = next(
        node
        for node in calendar_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "_handle_update"
    )

    assert [ast.unparse(item) for item in handler.decorator_list] == ["callback"]
    assert "async_update_event_listeners" not in ast.unparse(handler)


def test_calendar_expands_fixed_recurrences_inside_requested_range():
    store = FakeStore()
    store.tasks = [
        {
            "task_id": "daily-task",
            "task_name": "Water herbs",
            "task_due": "2026-07-22",
            "schedule_anchor_date": "2026-07-22",
            "schedule_type": "fixed",
            "schedule_unit": "daily",
            "schedule_interval": 2,
        }
    ]
    calendar = HomeTaskerCalendar(store)

    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 22, tzinfo=timezone.utc),
            datetime(2026, 7, 29, tzinfo=timezone.utc),
        )
    )

    assert [event.start for event in events] == [
        date(2026, 7, 22),
        date(2026, 7, 24),
        date(2026, 7, 26),
        date(2026, 7, 28),
    ]
    assert [event.uid for event in events] == [
        "daily-task:2026-07-22",
        "daily-task:2026-07-24",
        "daily-task:2026-07-26",
        "daily-task:2026-07-28",
    ]
    assert all(event.recurrence_id is None and event.rrule is None for event in events)


def test_calendar_projects_after_completion_recurrences_from_task_dues():
    store = FakeStore()
    store.tasks = [
        {
            "task_id": "sliding-task",
            "task_name": "Change filter",
            "task_due": "2026-07-22",
            "schedule_type": "sliding",
            "schedule_unit": "weekly",
            "schedule_interval": 2,
        }
    ]
    calendar = HomeTaskerCalendar(store)

    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 20, tzinfo=timezone.utc),
            datetime(2026, 8, 25, tzinfo=timezone.utc),
        )
    )

    assert [event.start for event in events] == [
        date(2026, 7, 22),
        date(2026, 8, 5),
        date(2026, 8, 19),
    ]


def test_invalid_legacy_recurrence_keeps_current_event_and_other_tasks():
    store = FakeStore()
    store.tasks = [
        {
            "task_id": "legacy-task",
            "task_name": "Legacy task",
            "task_due": "2026-07-22",
        },
        {
            "task_id": "valid-task",
            "task_name": "Valid task",
            "task_due": "2026-07-23",
            "schedule_anchor_date": "2026-07-23",
            "schedule_type": "fixed",
            "schedule_unit": "daily",
            "schedule_interval": 1,
        },
    ]
    calendar = HomeTaskerCalendar(store)

    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 22, tzinfo=timezone.utc),
            datetime(2026, 7, 25, tzinfo=timezone.utc),
        )
    )

    assert [(event.summary, event.start) for event in events] == [
        ("Legacy task", date(2026, 7, 22)),
        ("Valid task", date(2026, 7, 23)),
        ("Valid task", date(2026, 7, 24)),
    ]


def test_calendar_preserves_due_time_across_projected_occurrences():
    store = FakeStore()
    store.tasks = [
        {
            "task_id": "timed-task",
            "task_name": "Timed task",
            "task_due": "2026-07-24T08:00:00+00:00",
            "schedule_anchor_date": "2026-07-24",
            "schedule_type": "fixed",
            "schedule_unit": "daily",
            "schedule_interval": 1,
        }
    ]
    calendar = HomeTaskerCalendar(store)

    events = asyncio.run(
        calendar.async_get_events(
            None,
            datetime(2026, 7, 24, tzinfo=timezone.utc),
            datetime(2026, 7, 26, tzinfo=timezone.utc),
        )
    )

    assert [event.start for event in events] == [
        datetime(2026, 7, 24, 8, tzinfo=timezone.utc),
        datetime(2026, 7, 25, 8, tzinfo=timezone.utc),
    ]
