"""Test the Liquid Check sensor."""
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test sensor setup."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
