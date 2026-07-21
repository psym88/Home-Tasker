"""Home Tasker calendar tests."""

import asyncio
from datetime import date, datetime, timezone

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
        },
        {
            "id": "task-first-b",
            "name": "Clean sink",
            "description": None,
            "group_id": "group-1",
            "due_date": "2026-07-22",
        },
        {
            "id": "task-first-a",
            "name": "Clean counter",
            "description": None,
            "group_id": "group-1",
            "due_date": "2026-07-22",
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
