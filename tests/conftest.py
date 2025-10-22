"""Common fixtures for Liquid Check tests."""
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

# Must be before other imports for pytest plugin to work
pytest_plugins = "pytest_homeassistant_custom_component"  # noqa: E402

from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain="liquid_check",
        data={"name": "Test Liquid Check", "host": "192.168.1.100"},
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_setup_entry() -> Generator:
    """Override async_setup_entry."""
    with patch(
        "custom_components.liquid_check.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession with successful response."""

    def _create_mock(response_data, status=200):
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=response_data)

        mock_get = AsyncMock()
        mock_get.__aenter__.return_value = mock_response
        mock_get.__aexit__.return_value = None

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value = mock_get
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.__aexit__.return_value = None

        return patch(
            "custom_components.liquid_check.sensor.aiohttp.ClientSession",
            return_value=mock_session_instance,
        )

    return _create_mock
