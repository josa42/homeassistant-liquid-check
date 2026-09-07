"""Test the Liquid Check config flow."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)

GET_INFO = "custom_components.liquid_check.client.LiquidCheckClient.get_info"


async def test_form(hass: HomeAssistant):
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        "liquid_check", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)), patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "Test Device", "host": "192.168.1.100"},
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Device"
    assert result2["data"]["name"] == "Test Device"
    assert result2["data"]["host"] == "192.168.1.100"
    assert result2["data"]["scan_interval"] == 60  # default value
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_host(hass: HomeAssistant):
    """Test we handle invalid host error."""
    result = await hass.config_entries.flow.async_init(
        "liquid_check", context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Test Device", "host": "invalid host with spaces"},
    )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_host"}


async def test_form_cannot_connect(hass: HomeAssistant):
    """Test a device that does not answer is reported, not accepted."""
    result = await hass.config_entries.flow.async_init(
        "liquid_check", context={"source": config_entries.SOURCE_USER}
    )

    with patch(GET_INFO, AsyncMock(side_effect=OSError("Connection refused"))):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "Test Device", "host": "192.168.1.100"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(hass: HomeAssistant):
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        "liquid_check", context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.liquid_check.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "Test Device", "host": "192.168.1.100"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_with_custom_scan_interval(hass: HomeAssistant):
    """Test the user config flow with custom scan interval."""
    result = await hass.config_entries.flow.async_init(
        "liquid_check", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)), patch(
        "custom_components.liquid_check.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "Test Device", "host": "192.168.1.100", "scan_interval": 120},
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Device"
    assert result2["data"]["name"] == "Test Device"
    assert result2["data"]["host"] == "192.168.1.100"
    assert result2["data"]["scan_interval"] == 120
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_rejects_a_device_already_configured(hass: HomeAssistant):
    """Test the same physical device cannot be added twice."""
    for _ in range(2):
        result = await hass.config_entries.flow.async_init(
            "liquid_check", context={"source": config_entries.SOURCE_USER}
        )
        with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)), patch(
            "custom_components.liquid_check.async_setup_entry", return_value=True
        ):
            final = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {"name": "Test Device", "host": "192.168.1.100"},
            )
            await hass.async_block_till_done()

    assert final["type"] == data_entry_flow.FlowResultType.ABORT
    assert final["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries("liquid_check")) == 1


async def test_form_follows_a_device_to_a_new_address(hass: HomeAssistant):
    """Test re-adding a known device at a new address updates the stored host."""
    for host in ("192.168.1.100", "192.168.1.150"):
        result = await hass.config_entries.flow.async_init(
            "liquid_check", context={"source": config_entries.SOURCE_USER}
        )
        with patch(GET_INFO, AsyncMock(return_value=API_RESPONSE)), patch(
            "custom_components.liquid_check.async_setup_entry", return_value=True
        ):
            await hass.config_entries.flow.async_configure(
                result["flow_id"], {"name": "Test Device", "host": host}
            )
            await hass.async_block_till_done()

    entries = hass.config_entries.async_entries("liquid_check")
    assert len(entries) == 1
    assert entries[0].data["host"] == "192.168.1.150"


async def test_unique_id_falls_back_to_the_host(hass: HomeAssistant):
    """Test a device reporting no UUID is still identified by its address."""
    without_uuid = {"payload": {"device": {"firmware": "1.91"}}}

    result = await hass.config_entries.flow.async_init(
        "liquid_check", context={"source": config_entries.SOURCE_USER}
    )
    with patch(GET_INFO, AsyncMock(return_value=without_uuid)), patch(
        "custom_components.liquid_check.async_setup_entry", return_value=True
    ):
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"name": "Test Device", "host": "192.168.1.100"}
        )
        await hass.async_block_till_done()

    assert hass.config_entries.async_entries("liquid_check")[0].unique_id == (
        "192.168.1.100"
    )
