"""Home Tasker event helpers."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.core import Context, HomeAssistant, callback

from .const import EVENT_HOME_TASKER


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
    after_due = date.fromisoformat(after["due_date"]) <= today
    before_due = bool(
        before and date.fromisoformat(before["due_date"]) <= today
    )
    return after_due and not before_due


@callback
def async_fire_task_due_event(
    hass: HomeAssistant,
    task: dict[str, Any],
    source: str,
    *,
    context: Context | None = None,
) -> None:
    """Notify consumers that one task has just become due."""
    async_fire_home_tasker_event(
        hass,
        "due",
        "task",
        task["id"],
        context=context,
        resource_name=task.get("name"),
        group_id=task.get("group_id"),
        due_date=task["due_date"],
        source=source,
    )


@callback
def async_fire_change_or_due_event(
    hass: HomeAssistant,
    before: dict[str, Any] | None,
    after: dict[str, Any],
    today: date,
    source: str,
    fallback_action: str,
    fallback_resource_type: str,
    fallback_resource_id: str | None,
    *,
    context: Context | None = None,
    **fallback_data: Any,
) -> None:
    """Emit exactly one due-transition or ordinary change event."""
    if task_became_due(before, after, today):
        async_fire_task_due_event(hass, after, source, context=context)
        return
    async_fire_home_tasker_event(
        hass,
        fallback_action,
        fallback_resource_type,
        fallback_resource_id,
        context=context,
        **fallback_data,
    )
