"""Test the Liquid Check services."""
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_start_measure_service(hass: HomeAssistant):
    """Test the start_measure service."""
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_START_MEASURE,
        async_setup_entry,
    )
    
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    mock_entry.add_to_hass(hass)

    # Mock the platform forwarding to avoid coordinator threads
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=None):
        assert await async_setup_entry(hass, mock_entry)
        await hass.async_block_till_done()

    # Verify service is registered
    assert hass.services.has_service(DOMAIN, SERVICE_START_MEASURE)

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("custom_components.liquid_check.client.aiohttp.ClientSession", return_value=mock_session):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_MEASURE,
            {"device_id": mock_entry.entry_id},
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


async def test_start_measure_service_invalid_device(hass: HomeAssistant):
    """Test the start_measure service with invalid device ID."""
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_START_MEASURE,
        async_setup_entry,
    )
    
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    mock_entry.add_to_hass(hass)
    
    # Mock the platform forwarding
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=None):
        assert await async_setup_entry(hass, mock_entry)
        await hass.async_block_till_done()
    
    # Call service with non-existent device
    await hass.services.async_call(
        DOMAIN,
        SERVICE_START_MEASURE,
        {"device_id": "nonexistent"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_start_measure_service_connection_error(hass: HomeAssistant):
    """Test the start_measure service with connection error."""
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_START_MEASURE,
        async_setup_entry,
    )
    
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    mock_entry.add_to_hass(hass)

    # Mock the platform forwarding
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=None):
        assert await async_setup_entry(hass, mock_entry)
        await hass.async_block_till_done()

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=Exception("Connection error"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("custom_components.liquid_check.client.aiohttp.ClientSession", return_value=mock_session):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_MEASURE,
            {"device_id": mock_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()


async def test_restart_service(hass: HomeAssistant):
    """Test the restart service."""
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_RESTART,
        async_setup_entry,
    )
    
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    mock_entry.add_to_hass(hass)

    # Mock the platform forwarding to avoid coordinator threads
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=None):
        assert await async_setup_entry(hass, mock_entry)
        await hass.async_block_till_done()

    # Verify service is registered
    assert hass.services.has_service(DOMAIN, SERVICE_RESTART)

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("custom_components.liquid_check.client.aiohttp.ClientSession", return_value=mock_session):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESTART,
            {"device_id": mock_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Verify the POST request was made with correct parameters
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args
    
    assert call_args[0][0] == "http://192.168.1.100/command"
    assert call_args[1]["json"]["header"]["namespace"] == "Device.Control"
    assert call_args[1]["json"]["header"]["name"] == "Restart"
    assert call_args[1]["json"]["payload"] is None
    assert call_args[1]["headers"]["Content-Type"] == "application/json; charset=utf-8"


async def test_restart_service_invalid_device(hass: HomeAssistant):
    """Test the restart service with invalid device ID."""
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_RESTART,
        async_setup_entry,
    )
    
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    mock_entry.add_to_hass(hass)
    
    # Mock the platform forwarding
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=None):
        assert await async_setup_entry(hass, mock_entry)
        await hass.async_block_till_done()
    
    # Call service with non-existent device
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESTART,
        {"device_id": "nonexistent"},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_restart_service_connection_error(hass: HomeAssistant):
    """Test the restart service with connection error."""
    from custom_components.liquid_check import (
        DOMAIN,
        SERVICE_RESTART,
        async_setup_entry,
    )
    
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    mock_entry.add_to_hass(hass)

    # Mock the platform forwarding
    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups", return_value=None):
        assert await async_setup_entry(hass, mock_entry)
        await hass.async_block_till_done()

    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=Exception("Connection error"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("custom_components.liquid_check.client.aiohttp.ClientSession", return_value=mock_session):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESTART,
            {"device_id": mock_entry.entry_id},
            blocking=True,
        )
        await hass.async_block_till_done()
