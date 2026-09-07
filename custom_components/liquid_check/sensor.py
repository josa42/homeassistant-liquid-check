"""Sensor platform for Liquid Check integration."""
from __future__ import annotations

import logging

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
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import LiquidCheckDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Liquid Check sensor based on a config entry."""
    coordinator = entry.runtime_data

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


class LiquidCheckBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Liquid Check sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = coordinator.device_info


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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC
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
