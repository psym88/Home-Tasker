"""Admin-only WebSocket API."""

from datetime import timedelta
from functools import wraps
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOWNLOAD_URL, SIGNAL_UPDATED
from .helpers import get_store

TEXT = vol.Any(str, None)
GROUP_FIELDS = {vol.Required("name"): str, vol.Optional("manufacturer"): TEXT, vol.Optional("model"): TEXT, vol.Optional("icon"): TEXT, vol.Optional("description"): TEXT}
TASK_FIELDS = {
    vol.Required("name"): str,
    vol.Optional("description"): TEXT,
    vol.Required("due_date"): str,
    vol.Required("recurrence_mode"): vol.In(("fixed", "sliding")),
    vol.Required("frequency"): vol.In(("daily", "weekly", "monthly")),
    vol.Required("interval"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional("weekdays", default=[]): [vol.All(vol.Coerce(int), vol.Range(min=0, max=6))],
    vol.Optional("day_of_month"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=1, max=31)), "last", None),
}


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in COMMANDS:
        websocket_api.async_register_command(hass, command)


def require_store(func):
    @wraps(func)
    async def wrapper(hass, connection, msg):
        store = get_store(hass)
        if store is None:
            connection.send_error(msg["id"], "not_loaded", "Integration not loaded")
            return
        try:
            await func(hass, connection, msg, store)
        except (ValueError, KeyError) as err:
            connection.send_error(msg["id"], str(err), str(err))
    return wrapper


def updated(hass: HomeAssistant) -> None:
    async_dispatcher_send(hass, SIGNAL_UPDATED)


def validate_task_schedule(msg: dict[str, Any]) -> None:
    """Reject incomplete fixed calendar rules."""
    if msg.get("recurrence_mode") == "fixed" and msg.get("frequency") == "weekly" and not msg.get("weekdays"):
        raise ValueError("select_at_least_one_weekday")


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/list"})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_list(hass, connection, msg, store):
    connection.send_result(msg["id"], store.snapshot())


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/group/create", **GROUP_FIELDS})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_group_create(hass, connection, msg, store):
    connection.send_result(msg["id"], await store.async_add_group(msg)); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/group/update", vol.Required("group_id"): str, **{vol.Optional(k.schema): v for k, v in GROUP_FIELDS.items()}})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_group_update(hass, connection, msg, store):
    connection.send_result(msg["id"], await store.async_update_group(msg["group_id"], msg)); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/group/delete", vol.Required("group_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_group_delete(hass, connection, msg, store):
    await store.async_delete_group(msg["group_id"]); connection.send_result(msg["id"]); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/create", vol.Optional("group_id"): vol.Any(str, None), **TASK_FIELDS})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_create(hass, connection, msg, store):
    validate_task_schedule(msg)
    connection.send_result(msg["id"], await store.async_add_task(msg)); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/update", vol.Required("task_id"): str, **{vol.Optional(k.schema): v for k, v in TASK_FIELDS.items()}})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_update(hass, connection, msg, store):
    validate_task_schedule(msg)
    connection.send_result(msg["id"], await store.async_update_task(msg["task_id"], msg)); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/delete", vol.Required("task_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_delete(hass, connection, msg, store):
    await store.async_delete_task(msg["task_id"]); connection.send_result(msg["id"]); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/complete", vol.Required("task_id"): str, vol.Optional("completion_date"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_complete(hass, connection, msg, store):
    from homeassistant.util import dt as dt_util
    user = connection.user
    result = await store.async_complete_task(msg["task_id"], msg.get("completion_date", dt_util.now().date().isoformat()), user.id if user else None, user.name if user else "system")
    connection.send_result(msg["id"], result); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/history/list", vol.Required("task_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_history_list(hass, connection, msg, store):
    connection.send_result(msg["id"], {"history": store.history(msg["task_id"])})


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/history/delete", vol.Required("task_id"): str, vol.Required("entry_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_history_delete(hass, connection, msg, store):
    connection.send_result(msg["id"], await store.async_delete_history(msg["task_id"], msg["entry_id"])); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/attachment/delete", vol.Required("attachment_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_attachment_delete(hass, connection, msg, store):
    await store.async_delete_attachment(msg["attachment_id"]); connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/attachment/sign", vol.Required("attachment_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_attachment_sign(hass, connection, msg, store):
    attachment_id = msg["attachment_id"]
    if store.attachment(attachment_id) is None or not store.file_path(attachment_id).exists():
        raise ValueError("unknown_attachment")
    path = f"{DOWNLOAD_URL}/{attachment_id}"
    url = async_sign_path(hass, path, timedelta(hours=1), refresh_token_id=connection.refresh_token_id)
    connection.send_result(msg["id"], {"url": url})


COMMANDS = (ws_list, ws_group_create, ws_group_update, ws_group_delete, ws_task_create, ws_task_update, ws_task_delete, ws_task_complete, ws_history_list, ws_history_delete, ws_attachment_delete, ws_attachment_sign)
