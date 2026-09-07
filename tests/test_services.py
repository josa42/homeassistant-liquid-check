"""Test the Liquid Check services."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.liquid_check import (
    DOMAIN,
    SERVICE_RESTART,
    SERVICE_START_MEASURE,
)

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)

ENTRY_ID = "test123"


@pytest.fixture
async def device_id(hass: HomeAssistant) -> str:
    """Set the integration up and return its device registry ID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test", "host": "192.168.1.100", "scan_interval": 60},
        entry_id=ENTRY_ID,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.get_info",
        AsyncMock(return_value=API_RESPONSE),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    return devices[0].id


@pytest.mark.parametrize(
    ("service", "command"),
    [(SERVICE_START_MEASURE, "StartMeasure"), (SERVICE_RESTART, "Restart")],
)
async def test_service_sends_command(
    hass: HomeAssistant, device_id: str, service: str, command: str
):
    """Test each service reaches the device behind the given device ID."""
    assert hass.services.has_service(DOMAIN, service)

    send_command = AsyncMock()
    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.send_command",
        send_command,
    ):
        await hass.services.async_call(
            DOMAIN, service, {"device_id": device_id}, blocking=True
        )
        await hass.async_block_till_done()

    send_command.assert_awaited_once_with(command)


@pytest.mark.parametrize("service", [SERVICE_START_MEASURE, SERVICE_RESTART])
async def test_service_rejects_config_entry_id(
    hass: HomeAssistant, device_id: str, service: str
):
    """Test a config entry ID is not accepted as a device ID.

    The device selector hands over a device registry ID. Matching against the
    config entry ID instead left both services dead from the UI, and the tests
    passed only because they supplied the entry ID themselves.
    """
    assert ENTRY_ID != device_id

    send_command = AsyncMock()
    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.send_command",
        send_command,
    ), pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, service, {"device_id": ENTRY_ID}, blocking=True
        )

    send_command.assert_not_awaited()


@pytest.mark.parametrize("service", [SERVICE_START_MEASURE, SERVICE_RESTART])
async def test_service_rejects_unknown_device(
    hass: HomeAssistant, device_id: str, service: str
):
    """Test an unknown device ID raises instead of failing silently."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, service, {"device_id": "does-not-exist"}, blocking=True
        )


@pytest.mark.parametrize("service", [SERVICE_START_MEASURE, SERVICE_RESTART])
async def test_service_surfaces_connection_failure(
    hass: HomeAssistant, device_id: str, service: str
):
    """Test an unreachable device fails the call rather than logging quietly."""
    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.send_command",
        AsyncMock(side_effect=OSError("Connection refused")),
    ), pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, service, {"device_id": device_id}, blocking=True
        )
