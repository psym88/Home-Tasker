"""History persistence tests."""

import asyncio

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
