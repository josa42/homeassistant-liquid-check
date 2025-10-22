"""Test the Liquid Check sensor."""
from unittest.mock import patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test sensor setup."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.PLATFORMS",
        [Platform.SENSOR],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    assert len(entries) == 1
    assert entries[0].unique_id == f"{mock_config_entry.entry_id}_liquid_check"
