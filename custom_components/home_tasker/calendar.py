"""Home Tasker calendar platform."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_UPDATED
from .models import HomeTaskerData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[HomeTaskerData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Home Tasker calendar."""
    async_add_entities([HomeTaskerCalendar(entry.runtime_data.store)])


class HomeTaskerCalendar(CalendarEntity):
    """Expose active task due dates as one Home Assistant calendar."""

    _attr_has_entity_name = True
    _attr_name = "Home Tasker"
    _attr_should_poll = False
    _attr_unique_id = f"{DOMAIN}_calendar"

    def __init__(self, store: Any) -> None:
        self._store = store

    def _calendar_event(self, task: dict[str, Any]) -> CalendarEvent:
        due = date.fromisoformat(task["due_date"])
        groups = {group["id"]: group for group in self._store.groups}
        group = groups.get(task.get("group_id"))
        return CalendarEvent(
            start=due,
            end=due + timedelta(days=1),
            summary=task["name"],
            description=task.get("description") or None,
            location=group["name"] if group else None,
            uid=task["id"],
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next task event."""
        today = dt_util.now().date()
        upcoming = sorted(
            (task for task in self._store.tasks if date.fromisoformat(task["due_date"]) >= today),
            key=lambda task: (task["due_date"], task["name"].casefold()),
        )
        return self._calendar_event(upcoming[0]) if upcoming else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return task due dates intersecting the requested local time range."""
        events: list[tuple[datetime, CalendarEvent]] = []
        for task in self._store.tasks:
            event = self._calendar_event(task)
            event_start = datetime.combine(event.start, time.min, tzinfo=start_date.tzinfo)
            event_end = datetime.combine(event.end, time.min, tzinfo=start_date.tzinfo)
            if event_end > start_date and event_start < end_date:
                events.append((event_start, event))
        return [event for _, event in sorted(events, key=lambda item: (item[0], item[1].summary.casefold()))]

    async def async_added_to_hass(self) -> None:
        """Refresh calendar state and active event subscriptions after mutations."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self._handle_update)
        )

    def _handle_update(self) -> None:
        self.async_write_ha_state()
        if update_listeners := getattr(self, "async_update_event_listeners", None):
            update_listeners()
