"""Data update coordinator for the Liquid Check integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import LiquidCheckClient
from .config_flow import scan_interval

_LOGGER = logging.getLogger(__name__)


class LiquidCheckDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Liquid Check data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.client = LiquidCheckClient(
            entry.data["host"], async_get_clientsession(hass)
        )
        interval = scan_interval(entry)
        
        # If interval is 0, disable automatic polling
        update_interval = None if interval == 0 else timedelta(seconds=interval)
        
        super().__init__(
            hass,
            _LOGGER,
            name="Liquid Check",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            data = await self.client.get_info()
            payload = data.get("payload", {})
            
            # Flatten the nested structure for easier access
            result = {}
            
            # Get measure data
            measure = payload.get("measure", {})
            result["level"] = measure.get("level")
            result["content"] = measure.get("content")
            result["percent"] = measure.get("percent")
            result["age"] = measure.get("age")
            
            # Get system data
            system = payload.get("system", {})
            result["error"] = system.get("error")
            result["uptime"] = system.get("uptime")
            
            # Get pump data
            pump = system.get("pump", {})
            result["totalRuns"] = pump.get("totalRuns")
            result["totalRuntime"] = pump.get("totalRuntime")
            
            # Get WiFi data
            wifi = payload.get("wifi", {})
            access_point = wifi.get("accessPoint", {})
            result["rssi"] = access_point.get("rssi")
            
            # Get device data
            device = payload.get("device", {})
            result["firmware"] = device.get("firmware")
            
            return result
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
