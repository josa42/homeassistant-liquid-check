"""Button platform for Liquid Check integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import LiquidCheckClient
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
            LiquidCheckStartMeasureButton(hass, entry),
            LiquidCheckRestartButton(hass, entry),
        ],
        True,
    )


class LiquidCheckBaseButton(ButtonEntity):
    """Base class for Liquid Check buttons."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._client = LiquidCheckClient(
            entry.data["host"], async_get_clientsession(hass)
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["name"],
            manufacturer="SI-Elektronik GmbH",
            model="Liquid-Check",
            configuration_url=f"http://{entry.data['host']}",
        )

    async def _send_command(self, command_name: str) -> None:
        """Send command to device."""
        await self._client.send_command(command_name)


class LiquidCheckStartMeasureButton(LiquidCheckBaseButton):
    """Button to start a measurement."""

    _attr_translation_key = "start_measurement"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_start_measure"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._send_command("StartMeasure")


class LiquidCheckRestartButton(LiquidCheckBaseButton):
    """Button to restart the device."""

    _attr_translation_key = "restart"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_restart"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._send_command("Restart")
