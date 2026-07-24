"""Tests for Home Tasker summary sensors."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from custom_components.home_tasker.sensor import TasksDueSensor


def test_tasks_due_counts_today_and_older():
    store = SimpleNamespace(
        tasks=[
            {"task_due": "2026-07-22"},
            {"task_due": "2026-07-23"},
            {"task_due": "2026-07-24"},
        ],
        is_due=lambda task, now: task["task_due"] <= now.date().isoformat(),
    )

    with patch(
        "custom_components.home_tasker.sensor.dt_util.utcnow",
        return_value=datetime(2026, 7, 23, 12, tzinfo=timezone.utc),
    ):
        sensor = TasksDueSensor(store)
        assert sensor.native_value == 2

    assert sensor.unique_id == "tasks_due"
    assert sensor.translation_key == "tasks_due"
    assert sensor.has_entity_name
    assert sensor.suggested_object_id == "tasks_due"
    assert sensor.device_info["name"] == "Home Tasker"
    assert sensor.device_info["identifiers"] == {("home_tasker", "home_tasker")}
    assert not sensor.should_poll
