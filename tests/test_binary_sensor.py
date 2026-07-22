from types import SimpleNamespace

from custom_components.home_tasker.binary_sensor import TaskSensor


def test_available_task_exposes_home_tasker_entity_type():
    store = SimpleNamespace(
        tasks=[
            {
                "id": "task-1",
                "group_id": "group-1",
                "name": "Clean kitchen",
                "due_date": "2026-07-22",
            }
        ]
    )

    attributes = TaskSensor(store, "task-1").extra_state_attributes

    assert attributes["home_tasker_entity_type"] == "task"
    assert attributes["task_id"] == "task-1"


def test_missing_task_exposes_no_state_attributes():
    sensor = TaskSensor(SimpleNamespace(tasks=[]), "deleted-task")

    assert sensor.extra_state_attributes == {}
