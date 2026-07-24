"""Home Tasker calendar platform."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import EVENT_HOME_TASKER
from .due import parse_task_due, task_due_date, task_due_datetime
from .entity import HOME_TASKER_DEVICE_INFO
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
    _attr_name = None
    _attr_should_poll = False
    _attr_unique_id = "calendar"
    _attr_device_info = HOME_TASKER_DEVICE_INFO

    def __init__(self, store: Any) -> None:
        self._store = store

    def _calendar_event(
        self, task: dict[str, Any], due: date | datetime | None = None
    ) -> CalendarEvent:
        due = due or parse_task_due(task["task_due"])
        duration = timedelta(minutes=1) if isinstance(due, datetime) else timedelta(days=1)
        return CalendarEvent(
            start=due,
            end=due + duration,
            summary=task["task_name"],
            description=task.get("task_description") or None,
            uid=f"{task['task_id']}:{due.isoformat()}",
        )

    @staticmethod
    def _next_occurrence(task: dict[str, Any], due: date) -> date:
        current = {**task, "task_due": due.isoformat()}
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
        original_due = parse_task_due(task["task_due"])
        due = task_due_date(task)
        while True:
            if isinstance(original_due, datetime):
                event_due: date | datetime = original_due.replace(
                    year=due.year, month=due.month, day=due.day
                )
                event_start = event_due
                event_end = event_start + timedelta(minutes=1)
            else:
                event_due = due
                event_start = dt_util.start_of_local_day(due)
                event_end = event_start + timedelta(days=1)
            if event_start >= end_date:
                break
            if event_end > start_date:
                events.append((event_start, self._calendar_event(task, event_due)))
            try:
                due = self._next_occurrence(task, due)
            except (KeyError, TypeError, ValueError):
                break
        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next task event."""
        now = dt_util.utcnow()
        upcoming = sorted(
            (task for task in self._store.tasks if task_due_datetime(task) >= now),
            key=lambda task: (task_due_datetime(task), task["task_name"].casefold()),
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
            self.hass.bus.async_listen(EVENT_HOME_TASKER, self._handle_update)
        )

    @callback
    def _handle_update(self, event: Event) -> None:
        self.async_write_ha_state()
