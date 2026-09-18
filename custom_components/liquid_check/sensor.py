"""Sensor platform for Liquid Check integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .config_flow import tolerance
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
            LiquidCheckWithdrawalSensor(coordinator, entry),
            LiquidCheckInflowSensor(coordinator, entry),
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


@dataclass
class CounterStoredData(ExtraStoredData):
    """The counter state that has to outlive a restart or a reload."""

    total: float
    mark: float | None

    def as_dict(self) -> dict[str, Any]:
        """Return the data to store."""
        return {"total": self.total, "mark": self.mark}

    @classmethod
    def from_dict(cls, stored: dict[str, Any]) -> CounterStoredData | None:
        """Return the stored data, or None if it cannot be read back."""
        try:
            mark = stored["mark"]
            return cls(float(stored["total"]), None if mark is None else float(mark))
        except (KeyError, TypeError, ValueError):
            return None


class LiquidCheckCounterSensor(LiquidCheckBaseSensor, RestoreEntity):
    """Base class for the sensors that add up the level changes in one direction.

    The device reports the content in steps, and a reading wobbles by a step
    without any liquid moving. So the counter keeps a mark and only books a
    change once the content is further than the tolerance away from it, in the
    direction the counter is interested in. A move in the other direction is
    not booked and takes the mark with it, which is what keeps the wobble from
    accumulating. Real changes below the tolerance are not lost either: they
    are booked as soon as they add up past it.
    """

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_suggested_display_precision = 0

    _key: str
    _counts_rise: bool

    def __init__(
        self, coordinator: LiquidCheckDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{self._key}"
        self._total = 0.0
        self._mark: float | None = None

    @property
    def native_value(self) -> float:
        """Return the liters counted so far."""
        return round(self._total, 1)

    @property
    def extra_restore_state_data(self) -> CounterStoredData:
        """Return the counter state to store."""
        return CounterStoredData(self._total, self._mark)

    async def async_added_to_hass(self) -> None:
        """Restore the counter, then take the current content as the mark."""
        if (stored := await self.async_get_last_extra_data()) is not None:
            if (restored := CounterStoredData.from_dict(stored.as_dict())) is not None:
                self._total = restored.total
                self._mark = restored.mark

        await super().async_added_to_hass()
        self._count()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Count the change this update brought, then write the state."""
        self._count()
        super()._handle_coordinator_update()

    def _count(self) -> None:
        """Book the content's distance from the mark, if it is far enough."""
        data = self.coordinator.data or {}
        content = data.get("content")
        if content is None:
            return

        content = float(content)
        if self._mark is None:
            self._mark = content
            return

        change = content - self._mark
        counted = change if self._counts_rise else -change

        if counted > tolerance(self._entry):
            self._total += counted
            self._mark = content
        elif counted < 0:
            # A move the other way is this counter's counterpart's business,
            # but the mark has to follow it so the wobble cannot add up.
            self._mark = content


class LiquidCheckWithdrawalSensor(LiquidCheckCounterSensor):
    """Representation of the liquid taken out of the tank."""

    _attr_translation_key = "withdrawal"
    _key = "withdrawal"
    _counts_rise = False


class LiquidCheckInflowSensor(LiquidCheckCounterSensor):
    """Representation of the liquid that went into the tank."""

    _attr_translation_key = "inflow"
    _key = "inflow"
    _counts_rise = True


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
