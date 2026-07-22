"""Task problem sensors."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_UPDATED
from .models import HomeTaskerData


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[HomeTaskerData], async_add_entities: AddEntitiesCallback) -> None:
    store = entry.runtime_data.store
    entities: dict[str, TaskSensor] = {}
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    async def sync() -> None:
        task_ids = {task["id"] for task in store.tasks}
        group_ids = {group["id"] for group in store.groups}

        for task_id in set(entities) - task_ids:
            entity = entities.pop(task_id)
            entity_id = entity.entity_id
            if entity_id is not None:
                await entity.async_remove(force_remove=True)
            if entity_id and entity_registry.async_get(entity_id):
                entity_registry.async_remove(entity_id)

        valid_unique_ids = {f"{DOMAIN}_{task_id}" for task_id in task_ids}
        for registry_entry in list(entity_registry.entities.values()):
            if (
                registry_entry.domain == "binary_sensor"
                and registry_entry.platform == DOMAIN
                and registry_entry.unique_id.startswith(f"{DOMAIN}_")
                and registry_entry.unique_id not in valid_unique_ids
            ):
                entity_registry.async_remove(registry_entry.entity_id)

        for device in list(device_registry.devices.values()):
            home_tasker_ids = {identifier[1] for identifier in device.identifiers if identifier[0] == DOMAIN}
            if home_tasker_ids and home_tasker_ids.isdisjoint(group_ids):
                device_registry.async_remove_device(device.id)

        groups = {group["id"]: group for group in store.groups}
        tasks = {task["id"]: task for task in store.tasks}
        for task_id, entity in entities.items():
            if entity.entity_id is None or entity.entity_id not in entity_registry.entities:
                continue
            group = groups.get(tasks[task_id]["group_id"])
            if group is None:
                continue
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, group["id"])},
                name=group["name"],
                manufacturer=group.get("manufacturer"),
                model=group.get("model"),
            )
            registry_entry = entity_registry.async_get(entity.entity_id)
            if registry_entry and registry_entry.device_id != device.id:
                moved_entry = entity_registry.async_update_entity(
                    entity.entity_id, device_id=device.id
                )
                new_entity_id = entity_registry.async_regenerate_entity_id(moved_entry)
                if new_entity_id != moved_entry.entity_id:
                    entity_registry.async_update_entity(
                        moved_entry.entity_id, new_entity_id=new_entity_id
                    )

        new = [TaskSensor(store, task_id) for task_id in task_ids - set(entities)]
        entities.update((entity._task_id, entity) for entity in new)
        if new:
            async_add_entities(new)

    await sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_UPDATED, sync))

    @callback
    def refresh_at_midnight(now) -> None:
        # Due state flips at the local date rollover without any mutation.
        async_dispatcher_send(hass, SIGNAL_UPDATED)

    entry.async_on_unload(
        async_track_time_change(hass, refresh_at_midnight, hour=0, minute=0, second=0)
    )


class TaskSensor(BinarySensorEntity):
    """One due-state entity per task."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True
    _attr_should_poll = False

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
        return bool(self._task and self._store.is_due(self._task, dt_util.now().date()))

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
        return {"home_tasker_entity_type": "task", "task_id": task["id"], **{k: task.get(k) for k in ("group_id", "assignee_user_id", "due_date", "start_date", "recurrence_mode", "frequency", "interval", "weekdays", "day_of_month", "month_of_year")}} if task else {}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self.async_write_ha_state))
