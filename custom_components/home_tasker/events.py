"""Home Tasker event helpers."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.core import Context, HomeAssistant, callback

from .const import EVENT_HOME_TASKER, EVENT_TASK_DUE


@callback
def async_fire_home_tasker_event(
    hass: HomeAssistant,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    *,
    context: Context | None = None,
    **data: Any,
) -> None:
    """Notify Home Assistant and frontend consumers about a stored change."""
    hass.bus.async_fire(
        EVENT_HOME_TASKER,
        {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            **data,
        },
        context=context,
    )


def task_became_due(
    before: dict[str, Any] | None,
    after: dict[str, Any],
    today: date,
) -> bool:
    """Return whether a task crossed from not due to due."""
    after_is_due = date.fromisoformat(after["due_date"]) <= today
    before_was_due = bool(
        before and date.fromisoformat(before["due_date"]) <= today
    )
    return after_is_due and not before_was_due


def tasks_becoming_due_at_midnight(
    tasks: list[dict[str, Any]], today: date
) -> list[dict[str, Any]]:
    """Return only tasks whose due state flips at this date rollover."""
    due_date = today.isoformat()
    return [task for task in tasks if task.get("due_date") == due_date]


@callback
def async_fire_task_due_event(
    hass: HomeAssistant,
    task: dict[str, Any],
    source: str,
    *,
    context: Context | None = None,
) -> None:
    """Notify consumers that one task has just become due."""
    hass.bus.async_fire(
        EVENT_TASK_DUE,
        {
            "task_id": task["id"],
            "task_name": task.get("name"),
            "group_id": task.get("group_id"),
            "due_date": task["due_date"],
            "source": source,
        },
        context=context,
    )
