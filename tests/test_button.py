"""Test the Liquid Check buttons."""
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.liquid_check import DOMAIN

from .conftest import FakeDevice

GET_INFO = "custom_components.liquid_check.client.LiquidCheckClient.get_info"
SEND_COMMAND = "custom_components.liquid_check.client.LiquidCheckClient.send_command"

START_MEASUREMENT = "button.test_start_measurement"
CONTENT = "sensor.test_content"


@pytest.fixture
async def setup_entry(hass: HomeAssistant, device: FakeDevice) -> MockConfigEntry:
    """Set up a config entry with polling disabled.

    Without polling, any reading after setup has to come from the button.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 0},
        entry_id="test123",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry


async def _press(hass: HomeAssistant, entity_id: str) -> None:
    """Press a button and wait for the press to finish."""
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    ("entity_id", "command"),
    [
        (START_MEASUREMENT, "StartMeasure"),
        ("button.test_restart", "Restart"),
    ],
)
async def test_button_sends_its_command(
    hass: HomeAssistant, setup_entry, device: FakeDevice, entity_id: str, command: str
):
    """Test each button sends the command it is named for."""
    assert hass.states.get(entity_id) is not None

    await _press(hass, entity_id)

    assert device.commands == [command]


async def test_measuring_waits_for_the_new_reading(
    hass: HomeAssistant, setup_entry, device: FakeDevice
):
    """Test the press returns with the new reading, not the one before it.

    A fetch right after the command still returns the previous reading, because
    the pump has not finished yet.
    """
    assert hass.states.get(CONTENT).state == "960"

    await _press(hass, START_MEASUREMENT)

    assert hass.states.get(CONTENT).state == "1234"
    assert device.polls > 2


async def test_measuring_rides_out_a_silent_device(
    hass: HomeAssistant, setup_entry, device: FakeDevice
):
    """Test a device that does not answer while measuring is waited for.

    The missed polls must not count as failed updates, or every sensor would
    flicker to unavailable during each measurement.
    """
    device.answers_while_measuring = False
    states = []
    hass.bus.async_listen(
        "state_changed", lambda event: states.append(event.data["new_state"].state)
    )

    await _press(hass, START_MEASUREMENT)

    assert hass.states.get(CONTENT).state == "1234"
    assert "unavailable" not in states


async def test_measuring_without_a_new_reading_fails(
    hass: HomeAssistant, setup_entry, device: FakeDevice
):
    """Test the press fails instead of leaving the old reading looking fresh."""
    device.finishes = False

    with pytest.raises(HomeAssistantError) as err:
        await _press(hass, START_MEASUREMENT)

    assert err.value.translation_key == "measurement_timeout"
    assert hass.states.get(CONTENT).state == "960"


async def test_restarting_does_not_refresh(
    hass: HomeAssistant, setup_entry, device: FakeDevice, freezer
):
    """Test restarting the device does not trigger a pointless refetch."""
    polls = device.polls

    await _press(hass, "button.test_restart")
    freezer.tick(timedelta(seconds=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert device.polls == polls


@pytest.mark.parametrize("entity_id", [START_MEASUREMENT, "button.test_restart"])
async def test_button_surfaces_connection_failure(
    hass: HomeAssistant, setup_entry, entity_id: str
):
    """Test an unreachable device fails with a translated error, not a raw one."""
    with patch(
        SEND_COMMAND, AsyncMock(side_effect=OSError("Connection refused"))
    ), pytest.raises(HomeAssistantError) as err:
        await _press(hass, entity_id)

    assert err.value.translation_key == "command_failed"
