"""Tests for the Home Assistant-native task list."""

import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock

from homeassistant.components.todo import TodoItem, TodoItemStatus

from custom_components.home_tasker.todo import HomeTaskerTodoList


def task(**values):
    return {
        "task_id": "task-1",
        "task_name": "Clean kitchen",
        "task_description": "Use a damp cloth",
        "task_due": "2026-07-24",
        **values,
    }


def entity(store):
    hass = SimpleNamespace(
        bus=SimpleNamespace(async_fire=lambda *args, **kwargs: None),
        auth=SimpleNamespace(async_get_user=AsyncMock(return_value=None)),
    )
    return HomeTaskerTodoList(hass, store)


def test_tasks_are_native_todo_items_sorted_by_task_due():
    store = SimpleNamespace(
        tasks=[
            task(task_id="later", task_name="Later", task_due="2026-07-25"),
            task(task_id="first", task_name="First", task_due="2026-07-24"),
        ]
    )

    items = entity(store).todo_items

    assert [item.uid for item in items] == ["first", "later"]
    assert items[0] == TodoItem(
        uid="first",
        summary="First",
        description="Use a damp cloth",
        due=date(2026, 7, 24),
        status=TodoItemStatus.NEEDS_ACTION,
    )


def test_todo_preserves_an_exact_due_datetime():
    due = datetime(2026, 7, 24, 8, tzinfo=timezone.utc)
    item = entity(
        SimpleNamespace(tasks=[task(task_due=due.isoformat())])
    ).todo_items[0]

    assert item.due == due


def test_todo_list_uses_shared_device_and_counts_open_tasks():
    todo = entity(SimpleNamespace(tasks=[task(), task(task_id="task-2")]))

    assert todo.device_info["name"] == "Home Tasker"
    assert todo.device_info["identifiers"] == {("home_tasker", "home_tasker")}
    assert todo.state == 2
    assert todo.unique_id == "tasks"
    assert todo.name is None
    assert todo.has_entity_name


def test_completing_item_uses_home_tasker_completion_flow():
    completed = task(task_due="2026-08-24")
    store = SimpleNamespace(
        tasks=[task()],
        async_complete_task=AsyncMock(return_value=completed),
    )
    todo = entity(store)

    asyncio.run(
        todo.async_update_todo_item(
            TodoItem(
                uid="task-1",
                summary="Clean kitchen",
                status=TodoItemStatus.COMPLETED,
                due=date(2026, 7, 24),
            )
        )
    )

    store.async_complete_task.assert_awaited_once()


def test_rescheduling_item_updates_standard_fields_and_task_due():
    updated = task(
        task_name="Kitchen",
        task_description=None,
        task_due="2026-07-30",
    )
    store = SimpleNamespace(
        tasks=[task()],
        task=lambda task_id: task(),
        async_update_task=AsyncMock(return_value=updated),
    )
    todo = entity(store)

    asyncio.run(
        todo.async_update_todo_item(
            TodoItem(
                uid="task-1",
                summary="Kitchen",
                description=None,
                status=TodoItemStatus.NEEDS_ACTION,
                due=date(2026, 7, 30),
            )
        )
    )

    store.async_update_task.assert_awaited_once_with(
        "task-1",
        {
            "task_name": "Kitchen",
            "task_description": None,
            "task_due": "2026-07-30",
        },
        ANY,
    )
