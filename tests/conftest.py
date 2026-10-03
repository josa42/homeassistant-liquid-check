"""Common fixtures for Liquid Check tests."""
import copy
import json
from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Must be before other imports for pytest plugin to work
pytest_plugins = "pytest_homeassistant_custom_component"  # noqa: E402

from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

# Home Assistant's loader only finds the integration once custom_components has
# been imported. Doing it here keeps every test module independent of the order
# pytest happens to collect them in.
import custom_components.liquid_check  # noqa: E402,F401


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain="liquid_check",
        data={"name": "Test Liquid Check", "host": "192.168.1.100", "scan_interval": 60},
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_setup_entry() -> Generator:
    """Override async_setup_entry."""
    with patch(
        "custom_components.liquid_check.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


API_RESPONSE = json.loads(
    (Path(__file__).parent / "fixtures" / "api_response.json").read_text()
)


class FakeDevice:
    """A Liquid Check that has a new reading some seconds after StartMeasure.

    Until then it keeps answering with the previous reading, the way the real
    device does while its pump is running.
    """

    def __init__(self, freezer) -> None:
        """Start with the fixture reading and no measurement running."""
        self._freezer = freezer
        self.commands: list[str] = []
        self.polls = 0
        self.duration = timedelta(seconds=6)
        self.content = 1234
        self.answers_while_measuring = True
        self.finishes = True
        self._started: datetime | None = None

    def _now(self) -> datetime:
        """Return the frozen clock's time."""
        from homeassistant.util import dt as dt_util

        return dt_util.utcnow()

    async def send_command(self, command_name: str) -> None:
        """Record the command, and start measuring on StartMeasure."""
        self.commands.append(command_name)
        if command_name == "StartMeasure":
            self._started = self._now()

    async def get_info(self) -> dict:
        """Return the old reading until the measurement is done."""
        self.polls += 1
        response = copy.deepcopy(API_RESPONSE)
        if self._started is None:
            return response

        done = self._started + self.duration
        if not self.finishes or self._now() < done:
            if not self.answers_while_measuring:
                raise OSError("Connection refused")
            return response

        measure = response["payload"]["measure"]
        measure["content"] = self.content
        measure["age"] = int((self._now() - done).total_seconds())
        return response

    async def sleep(self, seconds: float) -> None:
        """Let time pass on the frozen clock instead of waiting for it."""
        self._freezer.tick(timedelta(seconds=seconds))


@pytest.fixture
def device(freezer) -> Generator[FakeDevice]:
    """Stand in for the Liquid Check device on the network."""
    fake = FakeDevice(freezer)
    with patch(
        "custom_components.liquid_check.client.LiquidCheckClient.get_info",
        AsyncMock(side_effect=fake.get_info),
    ), patch(
        "custom_components.liquid_check.client.LiquidCheckClient.send_command",
        AsyncMock(side_effect=fake.send_command),
    ), patch(
        "custom_components.liquid_check.coordinator.sleep", fake.sleep
    ):
        yield fake
