"""Test the Liquid Check buttons."""
import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.liquid_check import DOMAIN

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)

GET_INFO = "custom_components.liquid_check.client.LiquidCheckClient.get_info"
SEND_COMMAND = "custom_components.liquid_check.client.LiquidCheckClient.send_command"

# The coordinator debounces refresh requests; step past the cooldown.
PAST_COOLDOWN = timedelta(seconds=15)


@pytest.fixture
async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Set up a config entry with a stubbed device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 0},
        entry_id="test123",
    )
    entry.add_to_hass(hass)

    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


@pytest.mark.parametrize(
    ("entity_id", "command"),
    [
        ("button.test_start_measurement", "StartMeasure"),
        ("button.test_restart", "Restart"),
    ],
)
async def test_button_sends_its_command(
    hass: HomeAssistant, setup_entry, entity_id: str, command: str
):
    """Test each button sends the command it is named for."""
    assert hass.states.get(entity_id) is not None

    send_command = AsyncMock()
    with patch(SEND_COMMAND, send_command), patch(
        GET_INFO, AsyncMock(return_value=API_RESPONSE)
    ):
        await hass.services.async_call(
            BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        await hass.async_block_till_done()

    send_command.assert_awaited_once_with(command)


async def test_measuring_refreshes_the_sensors(
    hass: HomeAssistant, setup_entry, freezer
):
    """Test a measurement is refetched instead of waiting for the next poll.

    Polling is disabled for this entry, so any refetch has to come from the
    button press itself.
    """
    get_info = AsyncMock(return_value=API_RESPONSE)
    with patch(SEND_COMMAND, AsyncMock()), patch(GET_INFO, get_info):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.test_start_measurement"},
            blocking=True,
        )
        await hass.async_block_till_done()

        freezer.tick(PAST_COOLDOWN)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert get_info.await_count == 1


async def test_restarting_does_not_refresh(hass: HomeAssistant, setup_entry, freezer):
    """Test restarting the device does not trigger a pointless refetch."""
    get_info = AsyncMock(return_value=API_RESPONSE)
    with patch(SEND_COMMAND, AsyncMock()), patch(GET_INFO, get_info):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.test_restart"},
            blocking=True,
        )
        await hass.async_block_till_done()

        freezer.tick(PAST_COOLDOWN)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert get_info.await_count == 0
