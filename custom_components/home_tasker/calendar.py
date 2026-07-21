"""Home Tasker calendar platform."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_UPDATED
from .models import HomeTaskerData
from .scheduler import next_due


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

    def _calendar_event(
        self, task: dict[str, Any], due: date | None = None
    ) -> CalendarEvent:
        due = due or date.fromisoformat(task["due_date"])
        groups = {group["id"]: group for group in self._store.groups}
        group = groups.get(task.get("group_id"))
        return CalendarEvent(
            start=due,
            end=due + timedelta(days=1),
            summary=task["name"],
            description=task.get("description") or None,
            location=group["name"] if group else None,
            uid=task["id"],
            recurrence_id=due.isoformat(),
        )

    @staticmethod
    def _next_occurrence(task: dict[str, Any], due: date) -> date:
        current = {**task, "due_date": due.isoformat()}
        following = next_due(current, due)
        if following <= due:
            raise ValueError("recurrence_did_not_advance")
        return following

    def _task_events(
        self,
        task: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, CalendarEvent]]:
        """Expand one task without allowing invalid legacy data to break the feed."""
        events: list[tuple[datetime, CalendarEvent]] = []
        due = date.fromisoformat(task["due_date"])
        while True:
            event_start = datetime.combine(due, time.min, tzinfo=start_date.tzinfo)
            if event_start >= end_date:
                break
            event_end = event_start + timedelta(days=1)
            if event_end > start_date:
                events.append((event_start, self._calendar_event(task, due)))
            try:
                due = self._next_occurrence(task, due)
            except (KeyError, TypeError, ValueError):
                break
        return events

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
        """Return current and projected task occurrences in the requested range."""
        events: list[tuple[datetime, CalendarEvent]] = []
        for task in self._store.tasks:
            events.extend(self._task_events(task, start_date, end_date))
        return [event for _, event in sorted(events, key=lambda item: (item[0], item[1].summary.casefold()))]

    async def async_added_to_hass(self) -> None:
        """Refresh calendar state and active event subscriptions after mutations."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
