"""Button platform for Liquid Check integration."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Liquid Check button based on a config entry."""
    async_add_entities(
        [
            LiquidCheckStartMeasureButton(entry),
            LiquidCheckRestartButton(entry),
        ],
        True,
    )


class LiquidCheckBaseButton(ButtonEntity):
    """Base class for Liquid Check buttons."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Liquid-Check",
            manufacturer="SI-Elektronik GmbH",
            model="Liquid-Check",
        )

    async def _send_command(self, command_name: str) -> None:
        """Send command to device."""
        ip_address = self._entry.data["host"]
        url = f"http://{ip_address}/command"
        payload = {
            "header": {
                "namespace": "Device.Control",
                "name": command_name,
                "messageId": "1",
                "payloadVersion": "1",
            },
            "payload": None,
        }

        try:
            async with aiohttp.ClientSession() as session, session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
        except Exception as err:
            _LOGGER.error("Failed to send %s command: %s", command_name, err)
            raise


class LiquidCheckStartMeasureButton(LiquidCheckBaseButton):
    """Button to start a measurement."""

    _attr_name = "Start measurement"
    _attr_icon = "mdi:play"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_start_measure"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._send_command("StartMeasure")


class LiquidCheckRestartButton(LiquidCheckBaseButton):
    """Button to restart the device."""

    _attr_name = "Restart"
    _attr_icon = "mdi:restart"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_restart"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._send_command("Restart")
