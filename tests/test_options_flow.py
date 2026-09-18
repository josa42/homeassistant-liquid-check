"""Test the Liquid Check options flow."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.liquid_check import DOMAIN
from custom_components.liquid_check.config_flow import scan_interval, tolerance

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)

GET_INFO = "custom_components.liquid_check.client.LiquidCheckClient.get_info"


async def _setup(hass: HomeAssistant, **data) -> MockConfigEntry:
    """Set up a config entry with a stubbed device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", **data},
        entry_id="test123",
    )
    entry.add_to_hass(hass)

    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_options_flow_changes_the_poll_interval(hass: HomeAssistant):
    """Test the interval can be changed without removing the device."""
    entry = await _setup(hass, scan_interval=60)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 300}
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert scan_interval(entry) == 300


async def test_changing_options_reloads_the_coordinator(hass: HomeAssistant):
    """Test a new interval takes effect instead of waiting for a restart."""
    entry = await _setup(hass, scan_interval=60)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)) as get_info:
        await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 0}
        )
        await hass.async_block_till_done()

    # A reload refetches through a freshly built coordinator.
    assert get_info.await_count >= 1
    assert scan_interval(entry) == 0


async def test_options_default_to_the_setup_value(hass: HomeAssistant):
    """Test an entry created before the options flow existed still works."""
    entry = await _setup(hass, scan_interval=120)

    assert entry.options == {}
    assert scan_interval(entry) == 120


async def test_options_flow_changes_the_tolerance(hass: HomeAssistant):
    """Test the counting tolerance can be matched to the tank."""
    entry = await _setup(hass, scan_interval=60)
    assert tolerance(entry) == 50

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 60, "tolerance": 120}
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert tolerance(entry) == 120


async def test_the_tolerance_survives_an_interval_change(hass: HomeAssistant):
    """Test the form keeps the stored tolerance rather than resetting it.

    The options flow replaces the whole options dict, so a form that dropped
    the tolerance would silently put every counter back to the default.
    """
    entry = await _setup(hass, scan_interval=60)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)):
        await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 60, "tolerance": 120}
        )
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["data_schema"]({})["tolerance"] == 120
