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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Liquid Check from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def handle_start_measure(call: ServiceCall) -> None:
        """Handle the start_measure service call."""
        device_id = call.data["device_id"]
        
        # Find the entry with matching device_id
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
        
        payload = {
            "header": {
                "namespace": "Device.Control",
                "name": "StartMeasure",
                "messageId": "1",
                "payloadVersion": "1"
            },
            "payload": None
        }
        
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json; charset=utf-8"}
                    ) as response:
                        if response.status == 200:
                            _LOGGER.info("Measurement started on device %s", host)
                        else:
                            _LOGGER.error(
                                "Failed to start measurement on device %s: status %s",
                                host,
                                response.status
                            )
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with device %s: %s", host, err)
        except Exception as err:
            _LOGGER.error("Unexpected error starting measurement on %s: %s", host, err)
    
    # Register the service
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_MEASURE,
        handle_start_measure,
        schema=SERVICE_START_MEASURE_SCHEMA,
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove service if no more entries
    if not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_START_MEASURE)
    
    return unload_ok
