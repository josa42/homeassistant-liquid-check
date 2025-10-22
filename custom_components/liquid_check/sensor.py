"""Sensor platform for Liquid Check integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = 60


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Liquid Check sensor based on a config entry."""
    coordinator = LiquidCheckDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            LiquidCheckLevelSensor(coordinator, entry),
            LiquidCheckContentSensor(coordinator, entry),
            LiquidCheckPercentSensor(coordinator, entry),
            LiquidCheckWiFiRSSISensor(coordinator, entry),
            LiquidCheckPumpTotalRunsSensor(coordinator, entry),
            LiquidCheckPumpTotalRuntimeSensor(coordinator, entry),
            LiquidCheckUptimeSensor(coordinator, entry),
            LiquidCheckErrorSensor(coordinator, entry),
            LiquidCheckFirmwareSensor(coordinator, entry),
            LiquidCheckMeasurementAgeSensor(coordinator, entry),
        ]
    )


class LiquidCheckDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Liquid Check data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.host = entry.data["host"]
        scan_interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name="Liquid Check",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        url = f"http://{self.host}/infos.json"
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise UpdateFailed(
                                f"Error fetching data: {response.status}"
                            )
                        data = await response.json()
                        payload = data.get("payload", {})
                        
                        # Flatten the nested structure for easier access
                        result = {}
                        
                        # Get measure data
                        measure = payload.get("measure", {})
                        result["level"] = measure.get("level")
                        result["content"] = measure.get("content")
                        result["percent"] = measure.get("percent")
                        result["age"] = measure.get("age")
                        
                        # Get system data
                        system = payload.get("system", {})
                        result["error"] = system.get("error")
                        result["uptime"] = system.get("uptime")
                        
                        # Get pump data
                        pump = system.get("pump", {})
                        result["totalRuns"] = pump.get("totalRuns")
                        result["totalRuntime"] = pump.get("totalRuntime")
                        
                        # Get WiFi data
                        wifi = payload.get("wifi", {})
                        access_point = wifi.get("accessPoint", {})
                        result["rssi"] = access_point.get("rssi")
                        
                        # Get device data
                        device = payload.get("device", {})
                        result["firmware"] = device.get("firmware")
                        
                        return result
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err


class LiquidCheckBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Liquid Check sensors."""

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={("liquid_check", entry.entry_id)},
            name=entry.data["name"],
            manufacturer="SI-Elektronik GmbH",
            model="Liquid Check Device",
            configuration_url=f"http://{entry.data['host']}",
        )


class LiquidCheckLevelSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Level Sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m"

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Level"
        self._attr_unique_id = f"{entry.entry_id}_level"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("level")
        return None


class LiquidCheckContentSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Content Sensor."""

    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Content"
        self._attr_unique_id = f"{entry.entry_id}_content"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("content")
        return None


class LiquidCheckPercentSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Percent Sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Percent"
        self._attr_unique_id = f"{entry.entry_id}_percent"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("percent")
        return None


class LiquidCheckWiFiRSSISensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check WiFi RSSI Sensor."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} WiFi RSSI"
        self._attr_unique_id = f"{entry.entry_id}_wifi_rssi"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("rssi")
        return None


class LiquidCheckPumpTotalRunsSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Pump Total Runs Sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Pump Total Runs"
        self._attr_unique_id = f"{entry.entry_id}_pump_total_runs"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("totalRuns")
        return None


class LiquidCheckPumpTotalRuntimeSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Pump Total Runtime Sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Pump Total Runtime"
        self._attr_unique_id = f"{entry.entry_id}_pump_total_runtime"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("totalRuntime")
        return None


class LiquidCheckUptimeSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Uptime Sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Uptime"
        self._attr_unique_id = f"{entry.entry_id}_uptime"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("uptime")
        return None


class LiquidCheckErrorSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Error Sensor."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Error"
        self._attr_unique_id = f"{entry.entry_id}_error"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("error")
        return None


class LiquidCheckFirmwareSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Firmware Sensor."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Firmware"
        self._attr_unique_id = f"{entry.entry_id}_firmware"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("firmware")
        return None


class LiquidCheckMeasurementAgeSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Measurement Age Sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = f"{entry.data['name']} Measurement Age"
        self._attr_unique_id = f"{entry.entry_id}_measurement_age"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("age")
        return None
