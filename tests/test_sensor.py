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
    from homeassistant.core import HomeAssistant

    from custom_components.liquid_check.sensor import LiquidCheckDataUpdateCoordinator
    
    hass = HomeAssistant("/test")
    coordinator = LiquidCheckDataUpdateCoordinator(hass, mock_config_entry)
    
    assert coordinator.host == "192.168.1.100"


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
        "level": 1.25,
        "content": 450.5,
        "percent": 42.3,
        "rssi": -65,
        "totalRuns": 1234,
        "totalRuntime": 86400,
        "uptime": 3600,
        "error": 0,
        "firmware": "1.2.3",
        "age": 120,
    }
    
    entry = MagicMock()
    entry.data = {"name": "Test", "host": "192.168.1.100"}
    entry.entry_id = "test123"
    
    # Test level sensor
    level_sensor = LiquidCheckLevelSensor(coordinator, entry)
    assert level_sensor._attr_device_class == "distance"
    assert level_sensor._attr_native_unit_of_measurement == "m"
    assert level_sensor._attr_state_class == "measurement"
    assert level_sensor.native_value == 1.25
    
    # Test content sensor
    content_sensor = LiquidCheckContentSensor(coordinator, entry)
    assert content_sensor._attr_device_class == "volume"
    assert content_sensor._attr_native_unit_of_measurement == UnitOfVolume.LITERS
    assert content_sensor._attr_state_class == "measurement"
    assert content_sensor.native_value == 450.5
    
    # Test percent sensor
    percent_sensor = LiquidCheckPercentSensor(coordinator, entry)
    assert percent_sensor._attr_native_unit_of_measurement == PERCENTAGE
    assert percent_sensor._attr_state_class == "measurement"
    assert percent_sensor.native_value == 42.3
    
    # Test WiFi RSSI sensor
    rssi_sensor = LiquidCheckWiFiRSSISensor(coordinator, entry)
    assert rssi_sensor._attr_device_class == "signal_strength"
    assert rssi_sensor._attr_native_unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    assert rssi_sensor._attr_state_class == "measurement"
    assert rssi_sensor.native_value == -65
    
    # Test pump total runs sensor
    runs_sensor = LiquidCheckPumpTotalRunsSensor(coordinator, entry)
    assert runs_sensor._attr_state_class == "total_increasing"
    assert runs_sensor.native_value == 1234
    
    # Test pump total runtime sensor
    runtime_sensor = LiquidCheckPumpTotalRuntimeSensor(coordinator, entry)
    assert runtime_sensor._attr_device_class == "duration"
    assert runtime_sensor._attr_native_unit_of_measurement == UnitOfTime.SECONDS
    assert runtime_sensor._attr_state_class == "total_increasing"
    assert runtime_sensor.native_value == 86400
    
    # Test uptime sensor
    uptime_sensor = LiquidCheckUptimeSensor(coordinator, entry)
    assert uptime_sensor._attr_device_class == "duration"
    assert uptime_sensor._attr_native_unit_of_measurement == UnitOfTime.SECONDS
    assert uptime_sensor._attr_state_class == "measurement"
    assert uptime_sensor.native_value == 3600
    
    # Test error sensor
    error_sensor = LiquidCheckErrorSensor(coordinator, entry)
    assert error_sensor.native_value == 0
    
    # Test firmware sensor
    firmware_sensor = LiquidCheckFirmwareSensor(coordinator, entry)
    assert firmware_sensor.native_value == "1.2.3"
    
    # Test measurement age sensor
    age_sensor = LiquidCheckMeasurementAgeSensor(coordinator, entry)
    assert age_sensor._attr_device_class == "duration"
    assert age_sensor._attr_native_unit_of_measurement == UnitOfTime.SECONDS
    assert age_sensor._attr_state_class == "measurement"
    assert age_sensor.native_value == 120


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
