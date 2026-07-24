"""Shared entity metadata for Home Tasker."""

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

HOME_TASKER_DEVICE_INFO = DeviceInfo(
    identifiers={(DOMAIN, DOMAIN)},
    name="Home Tasker",
    manufacturer="Home Tasker",
)
