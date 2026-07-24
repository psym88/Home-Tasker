"""Authenticated Home Tasker WebSocket API."""

from datetime import date, timedelta
from functools import wraps
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import DOWNLOAD_URL
from .due import task_due_date, task_due_with_date
from .events import async_fire_home_tasker_event
from .helpers import get_store
from .scheduler import due_sequence, next_due_sequence, validate_schedule

TEXT = vol.Any(str, None)
SCHEDULE_FIELDS = {
    vol.Required("schedule_type"): vol.In(("fixed", "sliding")),
    vol.Required("schedule_unit"): vol.In(("daily", "weekly", "monthly", "yearly")),
    vol.Required("schedule_interval"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    vol.Optional("schedule_weekdays", default=[]): [vol.All(vol.Coerce(int), vol.Range(min=0, max=6))],
    vol.Optional("schedule_day"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=1, max=31)), "last", None),
    vol.Optional("schedule_month"): vol.Any(vol.All(vol.Coerce(int), vol.Range(min=1, max=12)), None),
}
TASK_FIELDS = {
    vol.Required("task_name"): str,
    vol.Optional("task_description"): TEXT,
    vol.Optional("assignee_id"): TEXT,
    vol.Optional("nfc_tag_id"): TEXT,
    vol.Optional("schedule_start_date"): TEXT,
    vol.Optional("task_due"): str,
    **SCHEDULE_FIELDS,
}
PREVIEW_FIELDS = {
    vol.Optional("task_due"): str,
    vol.Optional("schedule_anchor_date"): str,
    vol.Optional("schedule_start_date"): TEXT,
    **SCHEDULE_FIELDS,
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


def updated(
    hass: HomeAssistant,
    connection,
    msg: dict[str, Any],
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    **data: Any,
) -> None:
    async_fire_home_tasker_event(
        hass,
        action,
        resource_type,
        resource_id,
        context=connection.context(msg),
        **data,
    )


def validate_task_schedule(
    msg: dict[str, Any], existing: dict[str, Any] | None = None
) -> None:
    """Reject incomplete fixed calendar rules."""
    values = {**(existing or {}), **msg}
    validate_schedule(values)


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/list"})
@websocket_api.async_response
@require_store
async def ws_list(hass, connection, msg, store):
    result = store.snapshot()
    result["today"] = dt_util.now().date().isoformat()
    result["signed_files"] = {
        item["attachment_id"]: async_sign_path(
            hass,
            f"{DOWNLOAD_URL}/{item['attachment_id']}",
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


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/create", **TASK_FIELDS})
@websocket_api.async_response
@require_store
async def ws_task_create(hass, connection, msg, store):
    validate_task_schedule(msg)
    today = dt_util.now().date()
    result = await store.async_add_task(msg, today)
    connection.send_result(msg["id"], result)
    updated(
        hass, connection, msg, "created", "task", result["task_id"],
        resource_name=result["task_name"],
    )


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/update", vol.Required("task_id"): str, **{vol.Optional(k.schema): v for k, v in TASK_FIELDS.items()}})
@websocket_api.async_response
@require_store
async def ws_task_update(hass, connection, msg, store):
    previous = store.task(msg["task_id"])
    validate_task_schedule(msg, previous)
    today = dt_util.now().date()
    result = await store.async_update_task(msg["task_id"], msg, today)
    connection.send_result(msg["id"], result)
    updated(
        hass, connection, msg, "updated", "task", msg["task_id"],
        resource_name=result["task_name"],
    )


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/task/delete", vol.Required("task_id"): str})
@websocket_api.async_response
@require_store
async def ws_task_delete(hass, connection, msg, store):
    task = store.task(msg["task_id"])
    await store.async_delete_task(msg["task_id"])
    connection.send_result(msg["id"])
    updated(
        hass, connection, msg, "deleted", "task", msg["task_id"],
        resource_name=task.get("task_name") if task else None,
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "home_tasker/task/preview_next_due", **PREVIEW_FIELDS}
)
@websocket_api.async_response
@require_store
async def ws_task_preview_next_due(hass, connection, msg, store):
    """Preview recurrence using the authoritative backend scheduler."""
    validate_schedule(msg)
    if msg.get("task_due"):
        current = task_due_date(msg)
        task_dues = [current, *next_due_sequence(msg, current, msg["count"] - 1)]
        serialized = [task_due_with_date(msg, due) for due in task_dues]
    else:
        task_dues = due_sequence(msg, dt_util.now().date(), msg["count"])
        serialized = [due.isoformat() for due in task_dues]
    connection.send_result(
        msg["id"],
        {"task_dues": serialized},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasker/task/complete",
        vol.Required("task_id"): str,
        vol.Optional("completion_date"): str,
        vol.Optional("notes"): TEXT,
    }
)
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
    connection.send_result(msg["id"], result)
    updated(
        hass, connection, msg, "completed", "task", msg["task_id"],
        resource_name=result.get("task_name"),
    )


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/history/list", vol.Required("task_id"): str})
@websocket_api.async_response
@require_store
async def ws_history_list(hass, connection, msg, store):
    connection.send_result(msg["id"], {"history": store.history(msg["task_id"])})


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/history/delete", vol.Required("task_id"): str, vol.Required("history_entry_id"): str})
@websocket_api.async_response
@require_store
async def ws_history_delete(hass, connection, msg, store):
    result = await store.async_delete_history(msg["task_id"], msg["history_entry_id"])
    connection.send_result(msg["id"], result)
    updated(
        hass, connection, msg, "deleted", "history", msg["history_entry_id"],
        task_id=msg["task_id"],
    )


@websocket_api.websocket_command({vol.Required("type"): "home_tasker/attachment/delete", vol.Required("attachment_id"): str})
@websocket_api.async_response
@require_store
async def ws_attachment_delete(hass, connection, msg, store):
    attachment = store.attachment(msg["attachment_id"])
    await store.async_delete_attachment(msg["attachment_id"])
    connection.send_result(msg["id"])
    updated(
        hass, connection, msg, "deleted", "attachment", msg["attachment_id"],
        task_id=attachment.get("task_id") if attachment else None,
    )


COMMANDS = (ws_list, ws_task_create, ws_task_update, ws_task_delete, ws_task_preview_next_due, ws_task_complete, ws_history_list, ws_history_delete, ws_attachment_delete)
