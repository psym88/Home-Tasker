"""Tests for task persistence normalization."""

import asyncio
from datetime import date

from custom_components.home_tasker.store import HomeTaskerStore


def _store(task):
    store = HomeTaskerStore.__new__(HomeTaskerStore)
    store._lock = asyncio.Lock()
    store._data = {"tasks": [task], "history": {}, "attachments": []}

    async def save():
        return None

    store._save = save
    return store


def _weekly_task():
    return {
        "task_id": "task",
        "task_name": "Task",
        "task_description": None,
        "assignee_id": None,
        "label_ids": [],
        "nfc_tag_id": None,
        "task_due": "2026-07-29",
        "schedule_start_date": None,
        "schedule_anchor_date": "2026-07-29",
        "schedule_type": "fixed",
        "schedule_unit": "weekly",
        "schedule_interval": 1,
        "schedule_weekdays": [2],
        "schedule_day": 29,
        "schedule_month": 7,
    }


def test_schedule_update_discards_inactive_values():
    async def run():
        store = _store(_weekly_task())
        updated = await store.async_update_task(
            "task",
            {
                "schedule_type": "fixed",
                "schedule_unit": "monthly",
                "schedule_interval": 1,
                "schedule_weekdays": [2],
                "schedule_day": 15,
                "schedule_month": 7,
            },
            date(2026, 7, 24),
        )

        assert updated["schedule_weekdays"] == []
        assert updated["schedule_day"] == 15
        assert updated["schedule_month"] is None

    asyncio.run(run())


def test_partial_schedule_update_merges_before_normalizing():
    async def run():
        task = _weekly_task()
        task["schedule_day"] = 29
        task["schedule_month"] = 7
        store = _store(task)

        updated = await store.async_update_task(
            "task", {"schedule_interval": 2}, date(2026, 7, 24)
        )

        assert updated["schedule_unit"] == "weekly"
        assert updated["schedule_weekdays"] == [2]
        assert updated["schedule_day"] is None
        assert updated["schedule_month"] is None

    asyncio.run(run())
