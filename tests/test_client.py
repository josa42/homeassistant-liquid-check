"""Test the Liquid Check HTTP client."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.liquid_check.client import LiquidCheckClient

API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)


def _mock_session(response: MagicMock) -> MagicMock:
    """Return a mock aiohttp session yielding the given response."""
    session = MagicMock()
    session.get = MagicMock(return_value=response)
    session.post = MagicMock(return_value=response)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


def _mock_response(**kwargs) -> MagicMock:
    """Return a mock aiohttp response."""
    response = MagicMock(status=200, **kwargs)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


async def test_get_info_requests_the_device():
    """Test get_info reads infos.json from the device."""
    session = _mock_session(_mock_response(json=AsyncMock(return_value=API_RESPONSE)))

    result = await LiquidCheckClient("192.168.1.100", session).get_info()

    assert result == API_RESPONSE
    assert session.get.call_args[0][0] == "http://192.168.1.100/infos.json"


@pytest.mark.parametrize("command", ["StartMeasure", "Restart"])
async def test_send_command_posts_the_documented_envelope(command: str):
    """Test send_command posts the envelope the device firmware expects."""
    session = _mock_session(_mock_response())

    await LiquidCheckClient("192.168.1.100", session).send_command(command)

    session.post.assert_called_once()
    args, kwargs = session.post.call_args

    assert args[0] == "http://192.168.1.100/command"
    assert kwargs["json"]["header"]["namespace"] == "Device.Control"
    assert kwargs["json"]["header"]["name"] == command
    assert kwargs["json"]["payload"] is None
    assert kwargs["headers"]["Content-Type"] == "application/json; charset=utf-8"


async def test_errors_propagate_to_the_caller():
    """Test transport failures are raised, not swallowed."""
    session = _mock_session(_mock_response())
    session.get = MagicMock(side_effect=OSError("Connection refused"))

    with pytest.raises(OSError):
        await LiquidCheckClient("192.168.1.100", session).get_info()
