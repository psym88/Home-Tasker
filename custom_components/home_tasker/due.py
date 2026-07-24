"""Shared task due-date and due-event handling."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import EVENT_HOME_TASKER
from .events import async_fire_home_tasker_event


def parse_task_due(value: str) -> date | datetime:
    """Parse a native Home Assistant date or datetime value."""
    if "T" not in value:
        return date.fromisoformat(value)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return parsed


def normalize_task_due(value: str) -> str:
    """Return a canonical native date or timezone-aware datetime string."""
    parsed = parse_task_due(value)
    return parsed.isoformat()


def task_due_datetime(task: dict[str, Any]) -> datetime:
    """Return a task's due value as an aware datetime."""
    due = parse_task_due(task["task_due"])
    if isinstance(due, datetime):
        return due
    return dt_util.start_of_local_day(due)


def task_due_date(task: dict[str, Any]) -> date:
    """Return the local calendar date of a task's due value."""
    due = parse_task_due(task["task_due"])
    if isinstance(due, datetime):
        return dt_util.as_local(due).date()
    return due


def task_due_with_date(task: dict[str, Any], value: date) -> str:
    """Move a due value to another date while preserving an optional time."""
    due = parse_task_due(task["task_due"])
    if isinstance(due, datetime):
        return due.replace(year=value.year, month=value.month, day=value.day).isoformat()
    return value.isoformat()


class TaskDueEventScheduler:
    """Fire one Home Tasker event for every task as it becomes due."""

    def __init__(self, hass: HomeAssistant, store: Any) -> None:
        self._hass = hass
        self._store = store
        self._cancel_timer = None
        self._cancel_listener = None

    @callback
    def start(self) -> None:
        """Start listening for task changes and schedule the next due time."""
        self._cancel_listener = self._hass.bus.async_listen(
            EVENT_HOME_TASKER, self._handle_event
        )
        self.reschedule()

    @callback
    def stop(self) -> None:
        """Stop event and time listeners."""
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None
        if self._cancel_listener:
            self._cancel_listener()
            self._cancel_listener = None

    @callback
    def _handle_event(self, event: Event) -> None:
        if event.data.get("action") != "task_due":
            self.reschedule()

    @callback
    def reschedule(self) -> None:
        """Keep exactly one timer for the nearest future due value."""
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None
        now = dt_util.utcnow()
        future = [
            due
            for task in self._store.tasks
            if (due := task_due_datetime(task)) > now
        ]
        if future:
            target = min(future)

            @callback
            def fire_due(fired_at: datetime) -> None:
                self._fire_due(target, fired_at)

            self._cancel_timer = async_track_point_in_time(
                self._hass,
                fire_due,
                target,
            )

    @callback
    def _fire_due(self, target: datetime, fired_at: datetime) -> None:
        """Fire each task due at the scheduled time and plan the next one."""
        self._cancel_timer = None
        for task in self._store.tasks:
            due = task_due_datetime(task)
            if target <= due <= fired_at:
                async_fire_home_tasker_event(
                    self._hass,
                    "task_due",
                    "task",
                    task["task_id"],
                    resource_name=task["task_name"],
                    task_due=task["task_due"],
                )
        self.reschedule()
