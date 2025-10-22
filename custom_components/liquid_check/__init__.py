"""The Liquid Check integration."""
from __future__ import annotations

import logging

import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

PLATFORMS: list[Platform] = [Platform.SENSOR]
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
    
    async def send_device_command(device_id: str, payload: dict, action: str) -> None:
        """Send a command to the Liquid Check device."""
        config_entry = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id == device_id:
                config_entry = entry
                break
        
        if not config_entry:
            _LOGGER.error("Device with ID %s not found", device_id)
            return
        
        host = config_entry.data["host"]
        url = f"http://{host}/command"
        
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json; charset=utf-8"}
                    ) as response:
                        if response.status == 200:
                            _LOGGER.info("%s on device %s", action, host)
                        else:
                            _LOGGER.error(
                                "Failed to %s on device %s: status %s",
                                action.lower(),
                                host,
                                response.status
                            )
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with device %s: %s", host, err)
        except Exception as err:
            _LOGGER.error("Unexpected error %s on %s: %s", action.lower(), host, err)
    
    def create_device_payload(name: str) -> dict:
        """Create a device control payload with the given command name."""
        return {
            "header": {
                "namespace": "Device.Control",
                "name": name,
                "messageId": "603D751B-EA6C0A2B",
                "correlationToken": "9224B227-BD79-8B46-3935-640D78F5339A",
                "payloadVersion": "1",
                "authorization": None
            },
            "payload": None
        }
    
    async def handle_start_measure(call: ServiceCall) -> None:
        """Handle the start_measure service call."""
        payload = create_device_payload("StartMeasure")
        await send_device_command(
            call.data["device_id"], payload, "Measurement started"
        )
    
    async def handle_restart(call: ServiceCall) -> None:
        """Handle the restart service call."""
        payload = create_device_payload("Restart")
        await send_device_command(
            call.data["device_id"], payload, "Device restarting"
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
