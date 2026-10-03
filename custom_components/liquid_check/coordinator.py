"""Data update coordinator for the Liquid Check integration."""
from __future__ import annotations

import logging
from asyncio import sleep
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, format_mac
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .client import LiquidCheckClient
from .config_flow import scan_interval
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MEASURE_POLL_INTERVAL = timedelta(seconds=2)
MEASURE_TIMEOUT = timedelta(seconds=60)


def _flatten(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten the device response into the values the entities read."""
    payload = data.get("payload") or {}
    
    # Flatten the nested structure for easier access
    result = {}
    
    # Get measure data
    measure = payload.get("measure") or {}
    result["level"] = measure.get("level")
    result["content"] = measure.get("content")
    result["percent"] = measure.get("percent")
    result["age"] = measure.get("age")
    result["maxLevel"] = (measure.get("tank") or {}).get("maxLevel")
    
    # Get system data
    system = payload.get("system") or {}
    result["error"] = system.get("error")
    result["uptime"] = system.get("uptime")
    
    # Get pump data
    pump = system.get("pump") or {}
    result["totalRuns"] = pump.get("totalRuns")
    result["totalRuntime"] = pump.get("totalRuntime")
    
    # Get WiFi data
    wifi = payload.get("wifi") or {}
    access_point = wifi.get("accessPoint") or {}
    result["rssi"] = access_point.get("rssi")
    result["ssid"] = access_point.get("ssid")
    
    # Get device data
    device = payload.get("device") or {}
    result["firmware"] = device.get("firmware")
    result["hardware"] = device.get("hardware")
    result["mac"] = (wifi.get("station") or {}).get("mac")
    
    return result


class LiquidCheckDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Liquid Check data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
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
            config_entry=entry,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            return _flatten(await self.client.get_info())
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def async_measure(self) -> None:
        """Take a measurement and publish its reading once the device has it.

        The pump runs for a while before the new reading exists, so a fetch
        right after the command still returns the previous one. Polling until
        the reading is younger than the command tells the two apart, and lets
        the caller rely on the sensors being current when this returns.
        """
        await self.async_send_command("StartMeasure")
        sent = dt_util.utcnow()

        while dt_util.utcnow() - sent < MEASURE_TIMEOUT:
            await sleep(MEASURE_POLL_INTERVAL.total_seconds())
            try:
                data = _flatten(await self.client.get_info())
            except Exception:
                # The device may not answer while the pump is running.
                continue

            elapsed = dt_util.utcnow() - sent
            age = data["age"]
            if age is not None and timedelta(seconds=age) < elapsed:
                self.async_set_updated_data(data)
                return

        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="measurement_timeout",
            translation_placeholders={
                "host": self.entry.data["host"],
                "seconds": str(int(MEASURE_TIMEOUT.total_seconds())),
            },
        )

    async def async_send_command(self, command_name: str) -> None:
        """Send a command to the device, failing with a user-facing error."""
        try:
            await self.client.send_command(command_name)
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"host": self.entry.data["host"]},
            ) from err

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device registry entry both platforms attach to."""
        data = self.data or {}

        connections = set()
        if mac := data.get("mac"):
            connections.add((CONNECTION_NETWORK_MAC, format_mac(mac)))

        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            connections=connections,
            name=self.entry.data["name"],
            manufacturer="SI-Elektronik GmbH",
            model="Liquid-Check",
            sw_version=data.get("firmware"),
            hw_version=data.get("hardware"),
            configuration_url=f"http://{self.entry.data['host']}",
        )
