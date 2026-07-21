"""Admin-only WebSocket API."""

from datetime import date, timedelta
from functools import wraps
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import DOWNLOAD_URL, SIGNAL_UPDATED
from .helpers import get_store
from .scheduler import due_sequence, next_due_sequence, validate_schedule

TEXT = vol.Any(str, None)
GROUP_FIELDS = {vol.Required("name"): str, vol.Optional("manufacturer"): TEXT, vol.Optional("model"): TEXT, vol.Optional("icon"): TEXT, vol.Optional("description"): TEXT}
TASK_FIELDS = {
    vol.Required("name"): str,
    vol.Optional("description"): TEXT,
    vol.Optional("assignee_user_id"): TEXT,
    vol.Optional("start_date"): TEXT,
    vol.Required("recurrence_mode"): vol.In(("fixed", "sliding")),
    vol.Required("frequency"): vol.In(("daily", "weekly", "monthly", "yearly")),
    vol.Required("interval"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional("weekdays", default=[]): [vol.All(vol.Coerce(int), vol.Range(min=0, max=6))],
    vol.Optional("day_of_month"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=1, max=31)), "last", None),
    vol.Optional("month_of_year"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=1, max=12)), None),
}
TASK_GROUP_FIELDS = {
    vol.Optional("group_id"): vol.Any(str, None),
    vol.Optional("group_name"): TEXT,
}
PREVIEW_FIELDS = {
    vol.Optional("due_date"): str,
    vol.Optional("schedule_anchor"): str,
    vol.Optional("start_date"): TEXT,
    vol.Required("recurrence_mode"): vol.In(("fixed", "sliding")),
    vol.Required("frequency"): vol.In(("daily", "weekly", "monthly", "yearly")),
    vol.Required("interval"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional("weekdays", default=[]): [
        vol.All(vol.Coerce(int), vol.Range(min=0, max=6))
    ],
    vol.Optional("day_of_month"): vol.Any(
        vol.All(vol.Coerce(int), vol.Range(min=1, max=31)), "last", None
    ),
    vol.Optional("month_of_year"): vol.Any(
        vol.All(vol.Coerce(int), vol.Range(min=1, max=12)), None
    ),
    vol.Optional("count", default=2): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
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


def validate_task_schedule(
    msg: dict[str, Any], existing: dict[str, Any] | None = None
) -> None:
    """Reject incomplete fixed calendar rules."""
    values = {**(existing or {}), **msg}
    validate_schedule(values)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/list"})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_list(hass, connection, msg, store):
    result = store.snapshot()
    result["today"] = dt_util.now().date().isoformat()
    result["signed_files"] = {
        item["id"]: async_sign_path(
            hass,
            f"{DOWNLOAD_URL}/{item['id']}",
            timedelta(hours=1),
            refresh_token_id=connection.refresh_token_id,
        )
        for item in result["attachments"]
    }
    result["users"] = [
        {"id": user.id, "name": user.name or user.id}
        for user in await hass.auth.async_get_users()
        if getattr(user, "is_active", True)
        and not getattr(user, "system_generated", False)
    ]
    connection.send_result(msg["id"], result)


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


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/create", **TASK_GROUP_FIELDS, **TASK_FIELDS})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_create(hass, connection, msg, store):
    validate_task_schedule(msg)
    today = dt_util.now().date()
    connection.send_result(msg["id"], await store.async_add_task(msg, today)); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/update", vol.Required("task_id"): str, **TASK_GROUP_FIELDS, **{vol.Optional(k.schema): v for k, v in TASK_FIELDS.items()}})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_update(hass, connection, msg, store):
    validate_task_schedule(msg, store.task(msg["task_id"]))
    today = dt_util.now().date()
    connection.send_result(msg["id"], await store.async_update_task(msg["task_id"], msg, today)); updated(hass)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/delete", vol.Required("task_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_delete(hass, connection, msg, store):
    await store.async_delete_task(msg["task_id"]); connection.send_result(msg["id"]); updated(hass)


@websocket_api.websocket_command(
    {vol.Required("type"): "home_tasker/task/preview_next_due", **PREVIEW_FIELDS}
)
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_preview_next_due(hass, connection, msg, store):
    """Preview recurrence using the authoritative backend scheduler."""
    validate_schedule(msg)
    if msg.get("due_date"):
        current = date.fromisoformat(msg["due_date"])
        due_dates = [current, *next_due_sequence(msg, current, msg["count"] - 1)]
    else:
        due_dates = due_sequence(msg, dt_util.now().date(), msg["count"])
    connection.send_result(
        msg["id"],
        {"due_dates": [due.isoformat() for due in due_dates]},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasker/task/complete",
        vol.Required("task_id"): str,
        vol.Optional("completion_date"): str,
        vol.Optional("notes"): TEXT,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_task_complete(hass, connection, msg, store):
    user = connection.user
    result = await store.async_complete_task(
        msg["task_id"],
        msg.get("completion_date", dt_util.now().date().isoformat()),
        user.id if user else None,
        user.name if user else "system",
        msg.get("notes"),
    )
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


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/attachment/sign_all"})
@websocket_api.require_admin
@websocket_api.async_response
@require_store
async def ws_attachment_sign_all(hass, connection, msg, store):
    connection.send_result(
        msg["id"],
        {
            "urls": {
                item["id"]: async_sign_path(
                    hass,
                    f"{DOWNLOAD_URL}/{item['id']}",
                    timedelta(hours=1),
                    refresh_token_id=connection.refresh_token_id,
                )
                for item in store.snapshot()["attachments"]
            }
        },
    )


COMMANDS = (ws_list, ws_group_create, ws_group_update, ws_group_delete, ws_task_create, ws_task_update, ws_task_delete, ws_task_preview_next_due, ws_task_complete, ws_history_list, ws_history_delete, ws_attachment_delete, ws_attachment_sign, ws_attachment_sign_all)
