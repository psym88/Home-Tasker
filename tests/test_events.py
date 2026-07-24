"""Public Home Tasker event tests."""

from types import SimpleNamespace

from custom_components.home_tasker.const import EVENT_HOME_TASKER
from custom_components.home_tasker.events import async_fire_home_tasker_event


def test_home_tasker_event_has_stable_filterable_data():
    fired = []
    context = object()
    hass = SimpleNamespace(
        bus=SimpleNamespace(
            async_fire=lambda event_type, data, context=None: fired.append(
                (event_type, data, context)
            )
        )
    )

    async_fire_home_tasker_event(
        hass,
        "completed",
        "task",
        "task-1",
        context=context,
        source="nfc",
    )

    assert fired == [
        (
            EVENT_HOME_TASKER,
            {
                "action": "completed",
                "resource_type": "task",
                "resource_id": "task-1",
                "source": "nfc",
            },
            context,
        )
    ]
