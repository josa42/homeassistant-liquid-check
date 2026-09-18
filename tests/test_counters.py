"""Test the sensors that count liquid taken out of and added to the tank."""
import copy
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.liquid_check import DOMAIN

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)

GET_INFO = "custom_components.liquid_check.client.LiquidCheckClient.get_info"

WITHDRAWAL = "sensor.test_withdrawal"
INFLOW = "sensor.test_inflow"


def _response(content: float) -> dict:
    """Return the device response for a given tank content."""
    data = copy.deepcopy(API_RESPONSE)
    data["payload"]["measure"]["content"] = content
    return data


async def _setup(hass: HomeAssistant, content: float, **options) -> MockConfigEntry:
    """Set up an entry whose device reports the given content."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100"},
        options=options,
        entry_id="test123",
    )
    entry.add_to_hass(hass)

    with patch(GET_INFO, AsyncMock(return_value=_response(content))):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def _report(hass: HomeAssistant, entry: MockConfigEntry, *contents: float) -> None:
    """Let the device report the given contents, one measurement after another."""
    for content in contents:
        with patch(GET_INFO, AsyncMock(return_value=_response(content))):
            await entry.runtime_data.async_refresh()
            await hass.async_block_till_done()


def _counted(hass: HomeAssistant, entity_id: str) -> float:
    """Return the liters a counter has booked."""
    return float(hass.states.get(entity_id).state)


async def test_counters_start_at_zero(hass: HomeAssistant):
    """Test the first reading only sets the mark."""
    await _setup(hass, 1800)

    assert _counted(hass, WITHDRAWAL) == 0
    assert _counted(hass, INFLOW) == 0


async def test_a_falling_level_counts_as_withdrawal(hass: HomeAssistant):
    """Test liquid leaving the tank is booked in full."""
    entry = await _setup(hass, 1800)

    await _report(hass, entry, 1680, 1600)

    assert _counted(hass, WITHDRAWAL) == 200
    assert _counted(hass, INFLOW) == 0


async def test_a_rising_level_counts_as_inflow(hass: HomeAssistant):
    """Test liquid entering the tank is booked in full."""
    entry = await _setup(hass, 2800)

    await _report(hass, entry, 2920, 3000)

    assert _counted(hass, INFLOW) == 200
    assert _counted(hass, WITHDRAWAL) == 0


async def test_a_wobbling_reading_counts_as_nothing(hass: HomeAssistant):
    """Test a reading stepping up and down on its own is not booked.

    The device reports in steps of 40 liters and a reading wobbles by one step
    for hours without any liquid moving, which would otherwise pile up into
    hundreds of liters a day.
    """
    entry = await _setup(hass, 1800)

    await _report(hass, entry, 1760, 1800, 1760, 1800, 1760, 1800)

    assert _counted(hass, WITHDRAWAL) == 0
    assert _counted(hass, INFLOW) == 0


async def test_small_withdrawals_are_booked_once_they_add_up(hass: HomeAssistant):
    """Test liquid taken out below the tolerance is delayed, not lost."""
    entry = await _setup(hass, 1800)

    await _report(hass, entry, 1760)
    assert _counted(hass, WITHDRAWAL) == 0

    await _report(hass, entry, 1720)
    assert _counted(hass, WITHDRAWAL) == 80


async def test_the_tolerance_is_configurable(hass: HomeAssistant):
    """Test a tank with coarser steps can raise the tolerance."""
    entry = await _setup(hass, 1800, tolerance=200)

    await _report(hass, entry, 1640)
    assert _counted(hass, WITHDRAWAL) == 0

    await _report(hass, entry, 1560)
    assert _counted(hass, WITHDRAWAL) == 240


async def test_counters_survive_a_restart(hass: HomeAssistant):
    """Test the totals and the mark are restored rather than restarted.

    Without the mark, the first reading after a restart would set a fresh one
    and the withdrawal it belongs to would go uncounted.
    """
    mock_restore_cache_with_extra_data(
        hass,
        (
            (State(WITHDRAWAL, "2000"), {"total": 2000.0, "mark": 1800.0}),
            (State(INFLOW, "500"), {"total": 500.0, "mark": 1800.0}),
        ),
    )

    entry = await _setup(hass, 1800)
    assert _counted(hass, WITHDRAWAL) == 2000
    assert _counted(hass, INFLOW) == 500

    await _report(hass, entry, 1600)
    assert _counted(hass, WITHDRAWAL) == 2200


async def test_counters_are_water_meters(hass: HomeAssistant):
    """Test both counters can feed the water dashboard and long-term statistics."""
    await _setup(hass, 1800)

    for entity_id in (WITHDRAWAL, INFLOW):
        state = hass.states.get(entity_id)
        assert state.attributes["device_class"] == "water"
        assert state.attributes["state_class"] == "total_increasing"
        assert state.attributes["unit_of_measurement"] == "L"
