"""Test the Liquid Check device actions."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_get_device_automations,
)

from custom_components.liquid_check import DOMAIN
from custom_components.liquid_check.device_action import (
    ACTION_TYPES,
    async_call_action_from_config,
)

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)


@pytest.fixture
async def device_id(hass: HomeAssistant) -> str:
    """Set the integration up and return its device registry ID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test123",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.get_info",
        AsyncMock(return_value=API_RESPONSE),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    return devices[0].id


async def test_actions_are_offered_for_the_device(hass: HomeAssistant, device_id: str):
    """Test Home Assistant lists both actions for a Liquid Check device."""
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_id
    )

    offered = {
        action[CONF_TYPE] for action in actions if action[CONF_DOMAIN] == DOMAIN
    }
    assert offered == ACTION_TYPES


@pytest.mark.parametrize(
    ("action_type", "command"),
    [("start_measure", "StartMeasure"), ("restart", "Restart")],
)
async def test_action_reaches_the_device(
    hass: HomeAssistant, device_id: str, action_type: str, command: str
):
    """Test running an action sends the command to the right device.

    The action passes a device registry ID straight through to the service, so
    this breaks whenever the service stops resolving that ID correctly.
    """
    send_command = AsyncMock()
    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.send_command",
        send_command,
    ):
        await async_call_action_from_config(
            hass,
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: action_type,
            },
            {},
            None,
        )
        await hass.async_block_till_done()

    send_command.assert_awaited_once_with(command)


async def test_every_action_type_has_a_name():
    """Test each action type is named in strings.json.

    An unnamed action type shows up as a raw key in the automation editor.
    """
    strings = json.loads(
        (
            Path(__file__).parent.parent
            / "custom_components"
            / "liquid_check"
            / "strings.json"
        ).read_text()
    )

    assert set(strings["device_automation"]["action_type"]) == ACTION_TYPES
