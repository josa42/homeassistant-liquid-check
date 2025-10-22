"""Test the Liquid Check sensor."""
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test basic sensor setup."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()


async def test_sensor_coordinator_url(mock_config_entry: MockConfigEntry):
    """Test coordinator uses correct URL from config."""
    from datetime import timedelta

    from homeassistant.core import HomeAssistant

    from custom_components.liquid_check.sensor import LiquidCheckDataUpdateCoordinator
    
    hass = HomeAssistant("/test")
    coordinator = LiquidCheckDataUpdateCoordinator(hass, mock_config_entry)
    
    assert coordinator.host == "192.168.1.100"
    assert coordinator.update_interval == timedelta(seconds=60)


async def test_sensor_coordinator_custom_interval():
    """Test coordinator uses custom scan interval."""
    from datetime import timedelta

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.liquid_check.sensor import LiquidCheckDataUpdateCoordinator
    
    entry = MockConfigEntry(
        domain="liquid_check",
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 120},
    )
    
    hass = HomeAssistant("/test")
    coordinator = LiquidCheckDataUpdateCoordinator(hass, entry)
    
    assert coordinator.update_interval == timedelta(seconds=120)


async def test_sensor_entities_have_correct_units():
    """Test sensor entities have correct device classes and units."""
    from unittest.mock import MagicMock

    from homeassistant.const import (
        PERCENTAGE,
        SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        UnitOfTime,
        UnitOfVolume,
    )

    from custom_components.liquid_check.sensor import (
        LiquidCheckContentSensor,
        LiquidCheckErrorSensor,
        LiquidCheckFirmwareSensor,
        LiquidCheckLevelSensor,
        LiquidCheckMeasurementAgeSensor,
        LiquidCheckPercentSensor,
        LiquidCheckPumpTotalRunsSensor,
        LiquidCheckPumpTotalRuntimeSensor,
        LiquidCheckUptimeSensor,
        LiquidCheckWiFiRSSISensor,
    )
    
    coordinator = MagicMock()
    coordinator.data = {
        "level": 0.24,
        "content": 960,
        "percent": 8.7,
        "rssi": -85,
        "totalRuns": 12,
        "totalRuntime": 43,
        "uptime": 7804,
        "error": 0,
        "firmware": "1.91",
        "age": 593,
    }
    
    entry = MagicMock()
    entry.data = {"name": "Test", "host": "192.168.1.100"}
    entry.entry_id = "test123"
    
    # Test level sensor
    level_sensor = LiquidCheckLevelSensor(coordinator, entry)
    assert level_sensor._attr_device_class == "distance"
    assert level_sensor._attr_native_unit_of_measurement == "m"
    assert level_sensor._attr_state_class == "measurement"
    assert level_sensor.native_value == 0.24
    
    # Test content sensor
    content_sensor = LiquidCheckContentSensor(coordinator, entry)
    assert content_sensor._attr_device_class == "volume"
    assert content_sensor._attr_native_unit_of_measurement == UnitOfVolume.LITERS
    assert content_sensor._attr_state_class == "measurement"
    assert content_sensor.native_value == 960
    
    # Test percent sensor
    percent_sensor = LiquidCheckPercentSensor(coordinator, entry)
    assert percent_sensor._attr_native_unit_of_measurement == PERCENTAGE
    assert percent_sensor._attr_state_class == "measurement"
    assert percent_sensor.native_value == 8.7
    
    # Test WiFi RSSI sensor
    rssi_sensor = LiquidCheckWiFiRSSISensor(coordinator, entry)
    assert rssi_sensor._attr_device_class == "signal_strength"
    assert rssi_sensor._attr_native_unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    assert rssi_sensor._attr_state_class == "measurement"
    assert rssi_sensor.native_value == -85
    
    # Test pump total runs sensor
    runs_sensor = LiquidCheckPumpTotalRunsSensor(coordinator, entry)
    assert runs_sensor._attr_state_class == "total_increasing"
    assert runs_sensor.native_value == 12
    
    # Test pump total runtime sensor
    runtime_sensor = LiquidCheckPumpTotalRuntimeSensor(coordinator, entry)
    assert runtime_sensor._attr_device_class == "duration"
    assert runtime_sensor._attr_native_unit_of_measurement == UnitOfTime.SECONDS
    assert runtime_sensor._attr_state_class == "total_increasing"
    assert runtime_sensor.native_value == 43
    
    # Test uptime sensor
    uptime_sensor = LiquidCheckUptimeSensor(coordinator, entry)
    assert uptime_sensor._attr_device_class == "duration"
    assert uptime_sensor._attr_native_unit_of_measurement == UnitOfTime.SECONDS
    assert uptime_sensor._attr_state_class == "measurement"
    assert uptime_sensor.native_value == 7804
    
    # Test error sensor
    error_sensor = LiquidCheckErrorSensor(coordinator, entry)
    assert error_sensor.native_value == 0
    
    # Test firmware sensor
    firmware_sensor = LiquidCheckFirmwareSensor(coordinator, entry)
    assert firmware_sensor.native_value == "1.91"
    
    # Test measurement age sensor
    age_sensor = LiquidCheckMeasurementAgeSensor(coordinator, entry)
    assert age_sensor._attr_device_class == "duration"
    assert age_sensor._attr_native_unit_of_measurement == UnitOfTime.SECONDS
    assert age_sensor._attr_state_class == "measurement"
    assert age_sensor.native_value == 593


async def test_sensor_handles_none_data():
    """Test sensors handle None data gracefully."""
    from unittest.mock import MagicMock

    from custom_components.liquid_check.sensor import LiquidCheckLevelSensor
    
    coordinator = MagicMock()
    coordinator.data = None
    
    entry = MagicMock()
    entry.data = {"name": "Test", "host": "192.168.1.100"}
    entry.entry_id = "test123"
    
    sensor = LiquidCheckLevelSensor(coordinator, entry)
    assert sensor.native_value is None


async def test_coordinator_parses_api_response():
    """Test that coordinator correctly parses the API response structure."""
    import json
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch

    from homeassistant.core import HomeAssistant

    from custom_components.liquid_check.sensor import LiquidCheckDataUpdateCoordinator
    
    # Load the fixture
    fixture_path = Path(__file__).parent / "fixtures" / "api_response.json"
    with open(fixture_path) as f:
        api_response = json.load(f)
    
    hass = HomeAssistant("/test")
    entry = MagicMock()
    entry.data = {"name": "Test", "host": "192.168.1.100"}
    
    coordinator = LiquidCheckDataUpdateCoordinator(hass, entry)
    
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=api_response)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await coordinator._async_update_data()
    
    # Verify the flattened structure
    assert result["level"] == 0.24
    assert result["content"] == 960
    assert result["percent"] == 8.7
    assert result["age"] == 593
    assert result["error"] == 0
    assert result["uptime"] == 7804
    assert result["totalRuns"] == 12
    assert result["totalRuntime"] == 43
    assert result["rssi"] == -85
    assert result["firmware"] == "1.91"
