"""Test the Liquid Check integration init."""
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test setup of a config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED


async def test_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test unload of a config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


async def test_services_outlive_the_config_entries(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test the domain services stay registered when an entry is unloaded.

    They are registered once in async_setup rather than per entry, so
    unloading one entry must not pull them out from under the others.
    """
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_RESTART,
        SERVICE_START_MEASURE,
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_START_MEASURE)
    assert hass.services.has_service(DOMAIN, SERVICE_RESTART)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_START_MEASURE)
    assert hass.services.has_service(DOMAIN, SERVICE_RESTART)


async def test_device_carries_the_reported_metadata(hass: HomeAssistant):
    """Test firmware, hardware and MAC land on the device, not just sensors."""
    import json
    from pathlib import Path
    from unittest.mock import AsyncMock

    from homeassistant.helpers import device_registry as dr

    from custom_components.liquid_check import DOMAIN

    api_response = json.loads(
        (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="metadata",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.get_info",
        AsyncMock(return_value=api_response),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    device = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)[0]

    assert device.sw_version == "1.91"
    assert device.hw_version == "C5"
    assert (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff") in device.connections
    assert device.configuration_url == "http://192.168.1.100"
    assert device.manufacturer == "SI-Elektronik GmbH"
