"""Test the sensor that reports when the device last started."""
import copy
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.liquid_check import DOMAIN

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)

GET_INFO = "custom_components.liquid_check.client.LiquidCheckClient.get_info"

LAST_BOOT = "sensor.test_last_boot"


def _response(uptime: int) -> dict:
    """Return the device response for a given uptime."""
    data = copy.deepcopy(API_RESPONSE)
    data["payload"]["system"]["uptime"] = uptime
    return data


async def _setup(hass: HomeAssistant, uptime: int) -> MockConfigEntry:
    """Set up an entry with the last boot sensor enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 0},
        entry_id="test123",
    )
    entry.add_to_hass(hass)

    # The sensor is disabled by default; register it enabled up front.
    er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, "test123_last_boot", suggested_object_id="test_last_boot"
    )

    with patch(GET_INFO, AsyncMock(return_value=_response(uptime))):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def _report(hass: HomeAssistant, entry: MockConfigEntry, uptime: int) -> None:
    """Let the device report the given uptime."""
    with patch(GET_INFO, AsyncMock(return_value=_response(uptime))):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()


def _last_boot(hass: HomeAssistant) -> datetime:
    """Return the boot time the sensor reports."""
    return dt_util.parse_datetime(hass.states.get(LAST_BOOT).state)


async def test_last_boot_is_now_minus_uptime(hass: HomeAssistant, freezer):
    """Test the boot time is derived from the reported uptime."""
    freezer.move_to("2026-10-03 12:00:00+00:00")
    await _setup(hass, 7804)

    state = hass.states.get(LAST_BOOT)
    assert state.attributes["device_class"] == "timestamp"
    assert "state_class" not in state.attributes
    assert _last_boot(hass) == dt_util.utcnow() - timedelta(seconds=7804)


async def test_last_boot_ignores_jitter(hass: HomeAssistant, freezer):
    """Test a few seconds of drift between polls do not write a new state."""
    freezer.move_to("2026-10-03 12:00:00+00:00")
    entry = await _setup(hass, 7804)
    before = _last_boot(hass)

    freezer.tick(timedelta(seconds=60))
    await _report(hass, entry, 7804 + 57)

    assert _last_boot(hass) == before


async def test_last_boot_follows_a_restart(hass: HomeAssistant, freezer):
    """Test a device restart moves the boot time forward."""
    freezer.move_to("2026-10-03 12:00:00+00:00")
    entry = await _setup(hass, 7804)

    freezer.tick(timedelta(hours=1))
    await _report(hass, entry, 30)

    assert _last_boot(hass) == dt_util.utcnow() - timedelta(seconds=30)


async def test_the_old_uptime_sensor_is_removed(hass: HomeAssistant):
    """Test the replaced uptime sensor does not linger as an orphaned entity."""
    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", DOMAIN, "test123_uptime")

    await _setup(hass, 7804)

    assert registry.async_get_entity_id("sensor", DOMAIN, "test123_uptime") is None
