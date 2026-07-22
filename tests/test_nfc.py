"""NFC tag assignment and completion tests."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from custom_components.home_tasker import nfc
from custom_components.home_tasker.store import HomeTaskerStore


class MemoryStore:
    async def async_save(self, data):
        self.data = data


def _store(tasks):
    store = HomeTaskerStore.__new__(HomeTaskerStore)
    store._lock = asyncio.Lock()
    store._store = MemoryStore()
    store._data = {
        "groups": [{"id": "group-1", "name": "Tasks"}],
        "tasks": tasks,
        "history": {},
        "attachments": [],
    }
    return store


def _task(task_id="task-1", tag_id=None):
    return {
        "id": task_id,
        "name": task_id,
        "group_id": "group-1",
        "nfc_tag_id": tag_id,
        "due_date": "2026-07-22",
        "recurrence_mode": "sliding",
        "frequency": "daily",
        "interval": 1,
    }


def test_tag_id_is_trimmed_and_unique():
    async def run():
        store = _store([_task(tag_id="existing")])
        payload = {
            **_task("new", "  tag-2  "),
            "recurrence_mode": "sliding",
            "frequency": "daily",
            "interval": 1,
        }
        created = await store.async_add_task(payload, date(2026, 7, 22))
        assert created["nfc_tag_id"] == "tag-2"
        with pytest.raises(ValueError, match="nfc_tag_already_assigned"):
            await store.async_update_task(created["id"], {"nfc_tag_id": "existing"})

    asyncio.run(run())


def test_matching_scan_completes_task_with_event_user(monkeypatch):
    async def run():
        store = _store([_task(tag_id="tag-1")])
        user = SimpleNamespace(id="user-1", name="Alex")
        hass = SimpleNamespace(
            auth=SimpleNamespace(async_get_user=lambda user_id: _async_value(user))
        )
        event = SimpleNamespace(
            data={"tag_id": "tag-1", "device_id": "reader-1"},
            context=SimpleNamespace(user_id="user-1"),
        )
        updates = []
        monkeypatch.setattr(
            nfc, "async_fire_home_tasker_event", lambda *args, **kwargs: updates.append((args, kwargs))
        )
        await nfc.async_handle_tag_scanned(hass, store, event)
        history = store.history("task-1")
        assert len(history) == 1
        assert history[0]["user_id"] == "user-1"
        assert history[0]["user_name"] == "Alex"
        assert history[0]["notes"] == nfc.NFC_COMPLETION_NOTE
        assert updates == [
            (
                (hass, "completed", "task", "task-1"),
                {
                    "context": event.context,
                    "group_id": "group-1",
                    "resource_name": "task-1",
                    "source": "nfc",
                },
            )
        ]

    asyncio.run(run())


def test_unknown_scan_is_ignored(monkeypatch):
    async def run():
        store = _store([_task(tag_id="tag-1")])
        hass = SimpleNamespace(auth=None)
        event = SimpleNamespace(
            data={"tag_id": "other"}, context=SimpleNamespace(user_id=None)
        )
        updates = []
        monkeypatch.setattr(
            nfc, "async_fire_home_tasker_event", lambda *args, **kwargs: updates.append((args, kwargs))
        )
        await nfc.async_handle_tag_scanned(hass, store, event)
        assert store.history("task-1") == []
        assert updates == []

    asyncio.run(run())


async def _async_value(value):
    return value
