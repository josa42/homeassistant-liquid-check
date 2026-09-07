"""Test that entity translation keys, names and icons stay in sync."""
import json
from pathlib import Path
from unittest.mock import MagicMock

# Imported at module scope: custom_components is a namespace package, and the
# Home Assistant fixtures chdir away from the repo root before tests run.
from custom_components.liquid_check import button, sensor

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "liquid_check"


def _load(name: str) -> dict:
    """Load a JSON file from the component directory."""
    with open(COMPONENT_DIR / name) as file:
        return json.load(file)


def _entities() -> dict[str, list]:
    """Instantiate every entity, grouped by platform."""
    coordinator = MagicMock()
    coordinator.data = {}

    entry = MagicMock()
    entry.data = {"name": "Test", "host": "192.168.1.100"}
    entry.entry_id = "test123"

    return {
        "sensor": [
            cls(coordinator, entry)
            for cls in (
                sensor.LiquidCheckLevelSensor,
                sensor.LiquidCheckContentSensor,
                sensor.LiquidCheckPercentSensor,
                sensor.LiquidCheckWiFiRSSISensor,
                sensor.LiquidCheckPumpTotalRunsSensor,
                sensor.LiquidCheckPumpTotalRuntimeSensor,
                sensor.LiquidCheckUptimeSensor,
                sensor.LiquidCheckErrorSensor,
                sensor.LiquidCheckFirmwareSensor,
                sensor.LiquidCheckMeasurementAgeSensor,
            )
        ],
        "button": [
            cls(entry)
            for cls in (
                button.LiquidCheckStartMeasureButton,
                button.LiquidCheckRestartButton,
            )
        ],
    }


async def test_every_entity_has_a_translated_name():
    """Test each entity's translation key resolves to a name in strings.json.

    Without has_entity_name plus a translation key backed by strings.json, an
    entity falls back to an unnamed or English-only name.
    """
    strings = _load("strings.json")

    for platform, entities in _entities().items():
        for entity in entities:
            key = entity.translation_key
            assert key is not None, f"{type(entity).__name__} has no translation key"
            assert entity.has_entity_name, (
                f"{type(entity).__name__} sets a translation key but not "
                "has_entity_name, so the key is ignored"
            )
            assert key in strings["entity"][platform], (
                f"{type(entity).__name__} uses translation key '{key}' which is "
                f"missing from strings.json entity.{platform}"
            )


async def test_translations_match_strings():
    """Test translations/en.json carries the same entity keys as strings.json."""
    strings = _load("strings.json")["entity"]
    english = _load("translations/en.json")["entity"]

    assert strings == english


async def test_icons_reference_known_translation_keys():
    """Test icons.json only names translation keys that actually exist.

    An icon under an unknown key is silently ignored by Home Assistant, so a
    typo would leave the entity on its generic fallback icon.
    """
    icons = _load("icons.json")["entity"]
    known = {
        platform: {entity.translation_key for entity in entities}
        for platform, entities in _entities().items()
    }

    for platform, entries in icons.items():
        for key in entries:
            assert key in known[platform], (
                f"icons.json defines an icon for {platform} '{key}', but no such "
                "entity exists"
            )
