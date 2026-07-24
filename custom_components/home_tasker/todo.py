"""Home Assistant-native task list."""

from datetime import date, datetime

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import EVENT_HOME_TASKER
from .due import parse_task_due
from .entity import HOME_TASKER_DEVICE_INFO
from .events import async_fire_home_tasker_event
from .models import HomeTaskerData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[HomeTaskerData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the single Home Tasker to-do list."""
    entity = HomeTaskerTodoList(hass, entry.runtime_data.store)
    async_add_entities([entity])

    async def refresh(_event: Event) -> None:
        entity.refresh()

    entry.async_on_unload(hass.bus.async_listen(EVENT_HOME_TASKER, refresh))


class HomeTaskerTodoList(TodoListEntity):
    """Expose all Home Tasker tasks as one native to-do list."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_unique_id = "tasks"
    _attr_should_poll = False
    _attr_device_info = HOME_TASKER_DEVICE_INFO
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, hass: HomeAssistant, store) -> None:
        self._home_assistant = hass
        self._store = store

    @staticmethod
    def _task_due(value: date | datetime | None) -> date | datetime:
        return value or dt_util.now().date()

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=task["task_id"],
                summary=task["task_name"],
                description=task.get("task_description"),
                due=parse_task_due(task["task_due"]),
                status=TodoItemStatus.NEEDS_ACTION,
            )
            for task in sorted(
                self._store.tasks,
                key=lambda task: (
                    task["task_due"],
                    task["task_name"].casefold(),
                ),
            )
        ]

    def refresh(self) -> None:
        """Push the current store contents to Home Assistant."""
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    def _notify(
        self,
        action: str,
        task: dict,
        *,
        resource_name: str | None = None,
    ) -> None:
        async_fire_home_tasker_event(
            self._home_assistant,
            action,
            "task",
            task["task_id"],
            context=self._context,
            resource_name=resource_name or task.get("task_name"),
        )

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a task through Home Assistant's standard to-do API."""
        due = self._task_due(item.due)
        due_date = due.date() if isinstance(due, datetime) else due
        task = await self._store.async_add_task(
            {
                "task_name": item.summary,
                "task_description": item.description,
                "assignee_id": None,
                "nfc_tag_id": None,
                "task_due": due.isoformat(),
                "schedule_start_date": due_date.isoformat(),
                "schedule_type": "sliding",
                "schedule_unit": "monthly",
                "schedule_interval": 1,
                "schedule_weekdays": [],
                "schedule_day": None,
                "schedule_month": None,
            },
            dt_util.now().date(),
        )
        self._notify("created", task)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update or complete a task through Home Assistant's to-do API."""
        task_id = item.uid
        if task_id is None:
            raise ValueError("task_id_required")

        if item.status == TodoItemStatus.COMPLETED:
            user_id = getattr(self._context, "user_id", None)
            user = (
                await self._home_assistant.auth.async_get_user(user_id)
                if user_id
                else None
            )
            task = await self._store.async_complete_task(
                task_id,
                dt_util.now().date().isoformat(),
                user_id,
                user.name if user and user.name else "system",
            )
            self._notify("completed", task)
            return

        previous = self._store.task(task_id)
        due = self._task_due(item.due) if item.due is not None else None
        task = await self._store.async_update_task(
            task_id,
            {
                "task_name": item.summary,
                "task_description": item.description,
                **(
                    {"task_due": due.isoformat()}
                    if due is not None and due.isoformat() != previous["task_due"]
                    else {}
                ),
            },
            dt_util.now().date(),
        )
        self._notify("updated", task)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete tasks through Home Assistant's to-do API."""
        for task_id in uids:
            task = self._store.task(task_id)
            await self._store.async_delete_task(task_id)
            self._notify("deleted", task)
