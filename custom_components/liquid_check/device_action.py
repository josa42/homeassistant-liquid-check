"""Support for Liquid Check device actions."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ACTION_TYPES = {"start_measure", "restart"}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
    }
)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for Liquid Check devices."""
    return [
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: "start_measure",
        },
        {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: "restart",
        },
    ]


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, variables: dict, context: Context | None
) -> None:
    """Execute a device action."""
    service_data = {CONF_DEVICE_ID: config[CONF_DEVICE_ID]}
    
    if config[CONF_TYPE] == "start_measure":
        await hass.services.async_call(
            DOMAIN, "start_measure", service_data, blocking=True, context=context
        )
    elif config[CONF_TYPE] == "restart":
        await hass.services.async_call(
            DOMAIN, "restart", service_data, blocking=True, context=context
        )
