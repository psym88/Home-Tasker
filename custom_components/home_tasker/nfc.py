"""Complete Home Tasker tasks from Home Assistant tag scans."""

from __future__ import annotations

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import SIGNAL_UPDATED
from .store import HomeTaskerStore

EVENT_TAG_SCANNED = "tag_scanned"


async def async_handle_tag_scanned(
    hass: HomeAssistant, store: HomeTaskerStore, event: Event
) -> None:
    """Complete the task assigned to a scanned Home Assistant tag."""
    tag_id = str(event.data.get("tag_id") or "").strip()
    task = next((item for item in store.tasks if item.get("nfc_tag_id") == tag_id), None)
    if not tag_id or task is None:
        return

    user_id = event.context.user_id
    user = await hass.auth.async_get_user(user_id) if user_id else None
    await store.async_complete_task(
        task["id"],
        dt_util.now().date().isoformat(),
        user.id if user else None,
        user.name if user and user.name else "NFC tag",
    )
    async_dispatcher_send(hass, SIGNAL_UPDATED)


@callback
def async_setup_listener(hass: HomeAssistant, store: HomeTaskerStore):
    """Listen for Home Assistant tag scans for this config entry."""

    @callback
    def _handle_tag_scanned(event: Event) -> None:
        hass.async_create_task(async_handle_tag_scanned(hass, store, event))

    return hass.bus.async_listen(EVENT_TAG_SCANNED, _handle_tag_scanned)
