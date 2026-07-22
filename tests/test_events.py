"""Public Home Tasker event tests."""

from datetime import date
from types import SimpleNamespace

from custom_components.home_tasker.const import EVENT_HOME_TASKER
from custom_components.home_tasker.events import (
    async_fire_home_tasker_event,
    async_fire_task_due_event,
    task_became_due,
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


def test_task_due_event_exposes_notification_fields():
    fired = []
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

    async_fire_task_due_event(hass, task, "local_midnight")

    assert fired == [
        (
            EVENT_HOME_TASKER,
            {
                "action": "due",
                "resource_type": "task",
                "resource_id": "task-1",
                "resource_name": "Change filter",
                "group_id": "group-1",
                "due_date": "2026-07-23",
                "source": "local_midnight",
            },
            None,
        )
    ]
