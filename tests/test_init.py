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
