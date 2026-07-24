"""Typed runtime container for Home Tasker."""

from dataclasses import dataclass

from .due import TaskDueEventScheduler
from .store import HomeTaskerStore


@dataclass(slots=True)
class HomeTaskerData:
    """Runtime data stored on the config entry."""

    store: HomeTaskerStore
    due_scheduler: TaskDueEventScheduler

