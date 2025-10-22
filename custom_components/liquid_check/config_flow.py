"""Config flow for Liquid Check integration."""
from __future__ import annotations

import ipaddress
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("host"): str,
        vol.Optional("scan_interval", default=60): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=3600)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # Validate IP address or hostname
    host = data["host"].strip()
    
    # Try to parse as IP address first
    try:
        ipaddress.ip_address(host)
    except ValueError:
        # If not a valid IP, check if it looks like a hostname
        if not host or " " in host:
            raise InvalidHost
    
    # TODO: Add actual device connection test here
    # For now, we just validate the format
    
    return {"title": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain="liquid_check"):
    """Handle a config flow for Liquid Check."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidHost:
                errors["base"] = "invalid_host"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate the host/IP address is invalid."""
