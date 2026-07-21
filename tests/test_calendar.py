"""Home Tasker calendar tests."""

import ast
import asyncio
from datetime import date, datetime, timezone
from pathlib import Path

from custom_components.home_tasker.calendar import HomeTaskerCalendar


class FakeStore:
    groups = [{"id": "group-1", "name": "Kitchen"}]
    tasks = [
        {
            "id": "task-later",
            "name": "Wipe shelves",
            "description": "Use a damp cloth",
            "group_id": "group-1",
            "due_date": "2026-07-24",
            "schedule_anchor": "2026-07-24",
            "recurrence_mode": "fixed",
            "frequency": "yearly",
            "interval": 1,
            "month_of_year": 7,
            "day_of_month": 24,
        },
        {
            "id": "task-first-b",
            "name": "Clean sink",
            "description": None,
            "group_id": "group-1",
            "due_date": "2026-07-22",
            "schedule_anchor": "2026-07-22",
            "recurrence_mode": "fixed",
            "frequency": "yearly",
            "interval": 1,
            "month_of_year": 7,
            "day_of_month": 22,
        },
        {
            "id": "task-first-a",
            "name": "Clean counter",
            "description": None,
            "group_id": "group-1",
            "due_date": "2026-07-22",
            "schedule_anchor": "2026-07-22",
            "recurrence_mode": "fixed",
            "frequency": "yearly",
            "interval": 1,
            "month_of_year": 7,
            "day_of_month": 22,
        },
    ]


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
    assert events[0].location == "Kitchen"
    assert events[0].uid == "task-first-a"
    assert events[0].recurrence_id == "2026-07-22"
    assert events[2].description == "Use a damp cloth"


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


def test_calendar_platform_is_forwarded_with_binary_sensors():
    from custom_components.home_tasker.const import PLATFORMS

    assert PLATFORMS == ["binary_sensor", "calendar"]


def test_calendar_dispatcher_update_is_an_event_loop_callback():
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
            "id": "daily-task",
            "name": "Water herbs",
            "group_id": "group-1",
            "due_date": "2026-07-22",
            "schedule_anchor": "2026-07-22",
            "recurrence_mode": "fixed",
            "frequency": "daily",
            "interval": 2,
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


def test_calendar_projects_after_completion_recurrences_from_due_dates():
    store = FakeStore()
    store.tasks = [
        {
            "id": "sliding-task",
            "name": "Change filter",
            "group_id": "group-1",
            "due_date": "2026-07-22",
            "recurrence_mode": "sliding",
            "frequency": "weekly",
            "interval": 2,
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
            "id": "legacy-task",
            "name": "Legacy task",
            "group_id": "group-1",
            "due_date": "2026-07-22",
        },
        {
            "id": "valid-task",
            "name": "Valid task",
            "group_id": "group-1",
            "due_date": "2026-07-23",
            "schedule_anchor": "2026-07-23",
            "recurrence_mode": "fixed",
            "frequency": "daily",
            "interval": 1,
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
