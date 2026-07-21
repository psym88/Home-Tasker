"""History persistence tests."""

import asyncio
from datetime import date

from custom_components.home_tasker.store import HomeTaskerStore


class MemoryStore:
    """Minimal Home Assistant Store replacement."""

    async def async_save(self, data):
        self.data = data


def test_completion_notes_are_trimmed_and_optional():
    async def run():
        store = HomeTaskerStore.__new__(HomeTaskerStore)
        store._lock = asyncio.Lock()
        store._store = MemoryStore()
        store._data = {
            "groups": [],
            "tasks": [
                {
                    "id": "task-1",
                    "due_date": "2026-07-21",
                    "recurrence_mode": "sliding",
                    "frequency": "daily",
                    "interval": 1,
                }
            ],
            "history": {},
            "attachments": [],
        }

        await store.async_complete_task(
            "task-1", "2026-07-21", "user-1", "Marco", "  Filter replaced  "
        )
        await store.async_complete_task(
            "task-1", "2026-07-22", "user-1", "Marco", "   "
        )

        history = store.history("task-1")
        assert {entry["notes"] for entry in history} == {"Filter replaced", None}
        assert all(entry["recorded_at"] for entry in history)

    asyncio.run(run())


def test_completing_task_sets_next_due_date_from_completion_date():
    async def run():
        store = HomeTaskerStore.__new__(HomeTaskerStore)
        store._lock = asyncio.Lock()
        store._store = MemoryStore()
        store._data = {
            "groups": [],
            "tasks": [
                {
                    "id": "task-1",
                    "due_date": "2026-07-21",
                    "recurrence_mode": "sliding",
                    "frequency": "monthly",
                    "interval": 1,
                }
            ],
            "history": {},
            "attachments": [],
        }

        completed = await store.async_complete_task(
            "task-1", "2026-07-25", "user-1", "Marco"
        )

        assert completed["due_date"] == "2026-08-25"
        assert store.history("task-1")[0]["due_after"] == "2026-08-25"
        assert store._store.data["tasks"][0]["due_date"] == "2026-08-25"

    asyncio.run(run())


def test_completing_calendar_task_early_keeps_upcoming_due_date():
    async def run():
        store = HomeTaskerStore.__new__(HomeTaskerStore)
        store._lock = asyncio.Lock()
        store._store = MemoryStore()
        store._data = {
            "groups": [],
            "tasks": [
                {
                    "id": "task-1",
                    "due_date": "2026-07-22",
                    "schedule_anchor": "2026-07-22",
                    "recurrence_mode": "fixed",
                    "frequency": "weekly",
                    "interval": 1,
                    "weekdays": [2],
                }
            ],
            "history": {},
            "attachments": [],
        }

        completed = await store.async_complete_task(
            "task-1", "2026-07-20", "user-1", "Marco"
        )

        assert completed["due_date"] == "2026-07-22"
        assert store.history("task-1")[0]["due_after"] == "2026-07-22"

    asyncio.run(run())


def test_store_calculates_initial_due_and_preserves_it_for_metadata_updates():
    async def run():
        store = HomeTaskerStore.__new__(HomeTaskerStore)
        store._lock = asyncio.Lock()
        store._store = MemoryStore()
        store._data = {
            "groups": [{"id": "group-1", "name": "Home"}],
            "tasks": [],
            "history": {},
            "attachments": [],
        }
        task = await store.async_add_task(
            {
                "group_id": "group-1",
                "name": "Bins",
                "description": None,
                "assignee_user_id": None,
                "start_date": None,
                "recurrence_mode": "fixed",
                "frequency": "weekly",
                "interval": 2,
                "weekdays": [3],
                "day_of_month": None,
                "month_of_year": None,
            },
            date(2026, 7, 21),
        )
        assert task["due_date"] == "2026-07-23"
        assert task["schedule_anchor"] == "2026-07-23"

        updated = await store.async_update_task(
            task["id"], {"name": "Recycling bins"}, date(2026, 7, 28)
        )
        assert updated["due_date"] == "2026-07-23"

        replanned = await store.async_update_task(
            task["id"], {"weekdays": [4]}, date(2026, 7, 28)
        )
        assert replanned["due_date"] == "2026-07-31"
        assert replanned["schedule_anchor"] == "2026-07-31"

    asyncio.run(run())
