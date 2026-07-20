"""Shared helpers."""

from homeassistant.core import HomeAssistant

from .const import DOMAIN


def get_store(hass: HomeAssistant):
    """Return the loaded singleton store."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries or not hasattr(entries[0], "runtime_data"):
        return None
    data = entries[0].runtime_data
    return getattr(data, "store", None)

