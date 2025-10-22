"""Test the Liquid Check sensor."""
from unittest.mock import AsyncMock, patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

MOCK_DATA = {
    "payload": {
        "measure": {
            "level": 0.23,
            "content": 920,
            "percent": 8.4,
        }
    }
}


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test sensor setup."""
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.liquid_check.PLATFORMS",
            [Platform.SENSOR],
        ),
        patch(
            "custom_components.liquid_check.sensor.aiohttp.ClientSession.get"
        ) as mock_get,
    ):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=MOCK_DATA)
        mock_get.return_value.__aenter__.return_value = mock_response

        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    assert len(entries) == 3
    unique_ids = {entry.unique_id for entry in entries}
    assert f"{mock_config_entry.entry_id}_level" in unique_ids
    assert f"{mock_config_entry.entry_id}_content" in unique_ids
    assert f"{mock_config_entry.entry_id}_percent" in unique_ids
