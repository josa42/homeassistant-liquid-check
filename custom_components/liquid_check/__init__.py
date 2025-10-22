"""The Liquid Check integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .client import LiquidCheckClient

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]
DOMAIN = "liquid_check"

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Liquid Check from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def send_device_command(
        device_id: str, command_name: str, action: str
    ) -> None:
        """Send a command to the Liquid Check device."""
        config_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id == device_id:
                config_entry = entry
                break
        
        if not config_entry:
            _LOGGER.error("Device with ID %s not found", device_id)
            return
        
        client = LiquidCheckClient(config_entry.data["host"])
        
        try:
            await client.send_command(command_name)
            _LOGGER.info("%s on device %s", action, config_entry.data["host"])
        except Exception as err:
            _LOGGER.error("Error %s on device: %s", action.lower(), err)
    
    async def handle_start_measure(call: ServiceCall) -> None:
        """Handle the start_measure service call."""
        await send_device_command(
            call.data["device_id"], "StartMeasure", "Measurement started"
        )
    
    async def handle_restart(call: ServiceCall) -> None:
        """Handle the restart service call."""
        await send_device_command(
            call.data["device_id"], "Restart", "Device restarting"
        )
    
    # Register the services
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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove services if no more entries
    if not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_START_MEASURE)
        hass.services.async_remove(DOMAIN, SERVICE_RESTART)
    
    return unload_ok
