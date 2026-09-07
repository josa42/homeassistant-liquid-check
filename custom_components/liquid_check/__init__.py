"""The Liquid Check integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .client import LiquidCheckClient
from .const import DOMAIN
from .coordinator import LiquidCheckDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

SERVICE_START_MEASURE = "start_measure"
SERVICE_START_MEASURE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
    }
)

SERVICE_RESTART = "restart"
SERVICE_RESTART_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
    }
)


def _config_entry_for_device(hass: HomeAssistant, device_id: str) -> ConfigEntry:
    """Return the config entry backing a device registry ID.

    Service calls carry the device registry ID handed over by the device
    selector, which is not the config entry ID.
    """
    device = dr.async_get(hass).async_get(device_id)
    if device is not None:
        for entry_id in device.config_entries:
            config_entry = hass.config_entries.async_get_entry(entry_id)
            if config_entry is not None and config_entry.domain == DOMAIN:
                return config_entry

    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="device_not_found",
        translation_placeholders={"device_id": device_id},
    )


async def _async_send_device_command(
    hass: HomeAssistant, device_id: str, command_name: str, action: str
) -> None:
    """Send a command to the Liquid Check device behind a device registry ID."""
    config_entry = _config_entry_for_device(hass, device_id)
    client = LiquidCheckClient(
        config_entry.data["host"], async_get_clientsession(hass)
    )

    try:
        await client.send_command(command_name)
        _LOGGER.info("%s on device %s", action, config_entry.data["host"])
    except Exception as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="command_failed",
            translation_placeholders={"host": config_entry.data["host"]},
        ) from err


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the Liquid Check services.

    The services address a device rather than a config entry, so they belong to
    the domain and are registered once instead of per entry.
    """

    async def handle_start_measure(call: ServiceCall) -> None:
        """Handle the start_measure service call."""
        await _async_send_device_command(
            hass, call.data["device_id"], "StartMeasure", "Measurement started"
        )

    async def handle_restart(call: ServiceCall) -> None:
        """Handle the restart service call."""
        await _async_send_device_command(
            hass, call.data["device_id"], "Restart", "Device restarting"
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_MEASURE,
        handle_start_measure,
        schema=SERVICE_START_MEASURE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTART,
        handle_restart,
        schema=SERVICE_RESTART_SCHEMA,
    )

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry so a changed poll interval takes effect."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Liquid Check from a config entry."""
    coordinator = LiquidCheckDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
