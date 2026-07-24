"""Summary sensors for Home Tasker."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import EVENT_HOME_TASKER
from .entity import HOME_TASKER_DEVICE_INFO
from .models import HomeTaskerData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[HomeTaskerData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    entity = TasksDueSensor(entry.runtime_data.store)
    async_add_entities([entity])

    async def refresh(_event: Event) -> None:
        entity.async_write_ha_state()

    entry.async_on_unload(hass.bus.async_listen(EVENT_HOME_TASKER, refresh))


class TasksDueSensor(SensorEntity):
    """Count tasks whose due time has been reached."""

    _attr_has_entity_name = True
    _attr_translation_key = "tasks_due"
    _attr_unique_id = "tasks_due"
    _attr_device_info = HOME_TASKER_DEVICE_INFO
    _attr_native_unit_of_measurement = "tasks"
    _attr_icon = "mdi:clipboard-alert-outline"
    _attr_should_poll = False

    def __init__(self, store) -> None:
        self._store = store

    @property
    def suggested_object_id(self) -> str:
        """Keep the entity ID stable across backend languages."""
        return "tasks_due"

    @property
    def native_value(self) -> int:
        now = dt_util.utcnow()
        return sum(self._store.is_due(task, now) for task in self._store.tasks)
