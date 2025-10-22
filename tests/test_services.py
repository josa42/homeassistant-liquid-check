"""Test the Liquid Check services."""
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_start_measure_service(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test the start_measure service."""
    mock_config_entry.add_to_hass(hass)

    # Set up the integration using config entries
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("custom_components.liquid_check.aiohttp.ClientSession", return_value=mock_session):
        await hass.services.async_call(
            "liquid_check",
            "start_measure",
            {"device_id": mock_config_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Verify the POST request was made with correct parameters
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args
    
    assert call_args[0][0] == "http://192.168.1.100/command"
    assert call_args[1]["json"]["header"]["namespace"] == "Device.Control"
    assert call_args[1]["json"]["header"]["name"] == "StartMeasure"
    assert call_args[1]["json"]["payload"] is None
    assert call_args[1]["headers"]["Content-Type"] == "application/json; charset=utf-8"
    
    # Clean up
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def test_start_measure_service_invalid_device(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test the start_measure service with invalid device ID."""
    mock_config_entry.add_to_hass(hass)
    
    # Set up the integration to register services
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    # Call service with non-existent device
    await hass.services.async_call(
        "liquid_check",
        "start_measure",
        {"device_id": "nonexistent"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_start_measure_service_connection_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test the start_measure service with connection error."""
    mock_config_entry.add_to_hass(hass)

    # Set up the integration to register services
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=Exception("Connection error"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("custom_components.liquid_check.aiohttp.ClientSession", return_value=mock_session):
        await hass.services.async_call(
            "liquid_check",
            "start_measure",
            {"device_id": mock_config_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()
