"""Common fixtures for Liquid Check tests."""
from collections.abc import Generator
from unittest.mock import patch

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
        data={"name": "Test Liquid Check"},
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_setup_entry() -> Generator:
    """Override async_setup_entry."""
    with patch(
        "custom_components.liquid_check.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
