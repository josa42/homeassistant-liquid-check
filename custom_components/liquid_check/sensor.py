"""Sensor platform for Liquid Check integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfLength,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .client import LiquidCheckClient
from .config_flow import scan_interval
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
        self._client = LiquidCheckClient(
            entry.data["host"], async_get_clientsession(hass)
        )
        interval = scan_interval(entry)
        
        # If interval is 0, disable automatic polling
        update_interval = None if interval == 0 else timedelta(seconds=interval)
        
        super().__init__(
            hass,
            _LOGGER,
            name="Liquid Check",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            data = await self._client.get_info()
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
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err


class LiquidCheckBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Liquid Check sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["name"],
            manufacturer="SI-Elektronik GmbH",
            model="Liquid-Check",
            configuration_url=f"http://{entry.data['host']}",
        )


class LiquidCheckLevelSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Level Sensor."""

    _attr_translation_key = "level"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.METERS

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_level"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("level")
        return None


class LiquidCheckContentSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Content Sensor."""

    _attr_translation_key = "content"
    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_content"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("content")
        return None


class LiquidCheckPercentSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Percent Sensor."""

    _attr_translation_key = "percent"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_percent"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("percent")
        return None


class LiquidCheckWiFiRSSISensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check WiFi RSSI Sensor."""

    _attr_translation_key = "wifi_rssi"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wifi_rssi"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("rssi")
        return None


class LiquidCheckPumpTotalRunsSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Pump Total Runs Sensor."""

    _attr_translation_key = "pump_total_runs"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pump_total_runs"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("totalRuns")
        return None


class LiquidCheckPumpTotalRuntimeSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Pump Total Runtime Sensor."""

    _attr_translation_key = "pump_total_runtime"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pump_total_runtime"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("totalRuntime")
        return None


class LiquidCheckUptimeSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Uptime Sensor."""

    _attr_translation_key = "uptime"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_uptime"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("uptime")
        return None


class LiquidCheckErrorSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Error Sensor."""

    _attr_translation_key = "error"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_error"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("error")
        return None


class LiquidCheckFirmwareSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Firmware Sensor."""

    _attr_translation_key = "firmware"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_firmware"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("firmware")
        return None


class LiquidCheckMeasurementAgeSensor(LiquidCheckBaseSensor):
    """Representation of Liquid Check Measurement Age Sensor."""

    _attr_translation_key = "measurement_age"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_measurement_age"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("age")
        return None
