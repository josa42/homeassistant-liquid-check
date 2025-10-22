"""Sensor platform for Liquid Check integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Liquid Check sensor based on a config entry."""
    async_add_entities([LiquidCheckSensor(entry)])


class LiquidCheckSensor(SensorEntity):
    """Representation of a Liquid Check Sensor."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._attr_name = f"{entry.data['name']} Liquid Check"
        self._attr_unique_id = f"{entry.entry_id}_liquid_check"
        self._attr_native_value = None
        self._host = entry.data["host"]

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        # TODO: Implement connection to device at self._host
        # Example:
        # response = await self.hass.async_add_executor_job(
        #     requests.get, f"http://{self._host}/api/status"
        # )
        # self._attr_native_value = response.json()["liquid_level"]
        pass
