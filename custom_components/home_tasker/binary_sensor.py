"""Task problem sensors."""

from datetime import date

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_UPDATED
from .models import HomeTaskerData


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[HomeTaskerData], async_add_entities: AddEntitiesCallback) -> None:
    store = entry.runtime_data.store
    known: set[str] = set()

    async def sync() -> None:
        new = [TaskSensor(store, task["id"]) for task in store.tasks if task["id"] not in known]
        known.update(entity._task_id for entity in new)
        if new:
            async_add_entities(new)

    await sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_UPDATED, sync))


class TaskSensor(BinarySensorEntity):
    """One due-state entity per task."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True

    def __init__(self, store, task_id: str) -> None:
        self._store = store
        self._task_id = task_id
        self._attr_unique_id = f"{DOMAIN}_{task_id}"

    @property
    def _task(self):
        return next((x for x in self._store.tasks if x["id"] == self._task_id), None)

    @property
    def available(self) -> bool:
        return self._task is not None

    @property
    def name(self) -> str | None:
        return self._task["name"] if self._task else None

    @property
    def is_on(self) -> bool:
        return bool(self._task and self._store.is_due(self._task, date.today()))

    @property
    def device_info(self) -> DeviceInfo | None:
        task = self._task
        if not task:
            return None
        group = next((x for x in self._store.groups if x["id"] == task["group_id"]), None)
        if not group:
            return None
        return DeviceInfo(identifiers={(DOMAIN, group["id"])}, name=group["name"], manufacturer=group.get("manufacturer"), model=group.get("model"))

    @property
    def extra_state_attributes(self):
        task = self._task
        return {"task_id": task["id"], **{k: task.get(k) for k in ("group_id", "due_date", "recurrence_mode", "frequency", "interval", "weekdays", "day_of_month")}} if task else {}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self.async_write_ha_state))
