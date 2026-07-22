"""Home Tasker event helpers."""

from __future__ import annotations

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
