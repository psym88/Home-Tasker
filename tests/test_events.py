"""Public Home Tasker event tests."""

import asyncio
from datetime import date
from types import SimpleNamespace

from custom_components.home_tasker import websocket
from custom_components.home_tasker.const import EVENT_HOME_TASKER, EVENT_TASK_DUE
from custom_components.home_tasker.events import (
    async_fire_home_tasker_event,
    async_fire_task_due_event,
    task_became_due,
    tasks_becoming_due_at_midnight,
)


def test_home_tasker_event_has_stable_filterable_data():
    fired = []
    context = object()
    hass = SimpleNamespace(
        bus=SimpleNamespace(
            async_fire=lambda event_type, data, context=None: fired.append(
                (event_type, data, context)
            )
        )
    )

    async_fire_home_tasker_event(
        hass,
        "completed",
        "task",
        "task-1",
        context=context,
        group_id="group-1",
        source="nfc",
    )

    assert fired == [
        (
            EVENT_HOME_TASKER,
            {
                "action": "completed",
                "resource_type": "task",
                "resource_id": "task-1",
                "group_id": "group-1",
                "source": "nfc",
            },
            context,
        )
    ]


def test_task_became_due_only_on_not_due_to_due_transition():
    today = date(2026, 7, 23)
    future = {"due_date": "2026-07-24"}
    due = {"due_date": "2026-07-23"}
    overdue = {"due_date": "2026-07-22"}

    assert task_became_due(None, due, today)
    assert task_became_due(future, due, today)
    assert task_became_due(future, overdue, today)
    assert not task_became_due(due, overdue, today)
    assert not task_became_due(overdue, due, today)
    assert not task_became_due(future, future, today)


def test_midnight_transition_excludes_already_overdue_and_future_tasks():
    tasks = [
        {"id": "overdue", "due_date": "2026-07-22"},
        {"id": "due-now", "due_date": "2026-07-23"},
        {"id": "future", "due_date": "2026-07-24"},
    ]

    assert tasks_becoming_due_at_midnight(tasks, date(2026, 7, 23)) == [tasks[1]]


def test_task_due_event_has_its_own_type_and_notification_fields():
    fired = []
    context = object()
    hass = SimpleNamespace(
        bus=SimpleNamespace(
            async_fire=lambda event_type, data, context=None: fired.append(
                (event_type, data, context)
            )
        )
    )
    task = {
        "id": "task-1",
        "name": "Change filter",
        "group_id": "group-1",
        "due_date": "2026-07-23",
    }

    async_fire_task_due_event(hass, task, "local_midnight", context=context)

    assert fired == [
        (
            EVENT_TASK_DUE,
            {
                "task_id": "task-1",
                "task_name": "Change filter",
                "group_id": "group-1",
                "due_date": "2026-07-23",
                "source": "local_midnight",
            },
            context,
        )
    ]


def test_task_update_keeps_change_event_and_adds_due_event_once(monkeypatch):
    async def run():
        today = date(2026, 7, 23)
        connection = SimpleNamespace(
            send_result=lambda *args: None,
            context=lambda msg: "request-context",
        )
        msg = {"id": 1, "task_id": "task-1"}
        events = []
        monkeypatch.setattr(
            websocket.dt_util,
            "now",
            lambda: SimpleNamespace(date=lambda: today),
        )
        monkeypatch.setattr(
            websocket,
            "updated",
            lambda *args, **kwargs: events.append(("changed", args, kwargs)),
        )
        monkeypatch.setattr(
            websocket,
            "async_fire_task_due_event",
            lambda *args, **kwargs: events.append(("due", args, kwargs)),
        )

        class TaskStore:
            def __init__(self, before, after):
                self.before = before
                self.after = after

            def task(self, task_id):
                return dict(self.before)

            async def async_update_task(self, task_id, payload, update_date):
                assert update_date == today
                return dict(self.after)

        future = {
            "id": "task-1",
            "name": "Change filter",
            "group_id": "group-1",
            "due_date": "2026-07-24",
            "recurrence_mode": "sliding",
        }
        due = {**future, "due_date": "2026-07-23"}
        handler = websocket.ws_task_update.__wrapped__.__wrapped__

        await handler(object(), connection, msg, TaskStore(future, due))
        assert [event[0] for event in events] == ["changed", "due"]

        events.clear()
        await handler(object(), connection, msg, TaskStore(due, due))
        assert [event[0] for event in events] == ["changed"]

    asyncio.run(run())
