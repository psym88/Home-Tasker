"""Home Tasker integration."""

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import http, websocket
from .const import DOMAIN, FRONTEND_URL, PANEL_JS_URL, PANEL_TITLE, PANEL_URL, PLATFORMS
from .models import HomeTaskerData
from .store import HomeTaskerStore


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    websocket.async_register(hass)
    http.async_register_views(hass)
    frontend_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths([StaticPathConfig(FRONTEND_URL, str(frontend_dir), False)])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    upload_dir = Path(hass.config.path(DOMAIN, "uploads"))
    store = HomeTaskerStore(hass, upload_dir)
    await store.async_load()
    entry.runtime_data = HomeTaskerData(store)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await panel_custom.async_register_panel(hass, webcomponent_name="home-tasker-panel", frontend_url_path=PANEL_URL.removeprefix("/"), module_url=PANEL_JS_URL, sidebar_title=PANEL_TITLE, sidebar_icon="mdi:clipboard-check-outline", require_admin=True, config={})
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        frontend.async_remove_panel(hass, PANEL_URL.removeprefix("/"))
    return unloaded
