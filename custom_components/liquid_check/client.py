"""Client for communicating with Liquid Check device."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class LiquidCheckClient:
    """Client to communicate with Liquid Check device."""

    def __init__(self, host: str) -> None:
        """Initialize the client."""
        self._host = host

    async def get_info(self) -> dict[str, Any]:
        """Get device information."""
        url = f"http://{self._host}/infos.json"
        try:
            async with aiohttp.ClientSession() as session, session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            _LOGGER.error("Failed to fetch data from %s: %s", url, err)
            raise

    async def send_command(self, command_name: str) -> None:
        """Send command to device."""
        url = f"http://{self._host}/command"
        payload = {
            "header": {
                "namespace": "Device.Control",
                "name": command_name,
                "messageId": "1",
                "payloadVersion": "1",
            },
            "payload": None,
        }

        try:
            async with aiohttp.ClientSession() as session, session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                response.raise_for_status()
        except Exception as err:
            _LOGGER.error("Failed to send %s command: %s", command_name, err)
            raise
