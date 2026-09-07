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


def _entities(hass) -> dict[str, list]:
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
            cls(hass, entry)
            for cls in (
                button.LiquidCheckStartMeasureButton,
                button.LiquidCheckRestartButton,
            )
        ],
    }


async def test_every_entity_has_a_translated_name(hass):
    """Test each entity's translation key resolves to a name in strings.json.

    Without has_entity_name plus a translation key backed by strings.json, an
    entity falls back to an unnamed or English-only name.
    """
    strings = _load("strings.json")

    for platform, entities in _entities(hass).items():
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


def _key_paths(value, prefix: str = "") -> set[str]:
    """Collect the dotted path of every leaf key in a nested dict."""
    if not isinstance(value, dict):
        return {prefix}
    return {
        path
        for key, child in value.items()
        for path in _key_paths(child, f"{prefix}.{key}" if prefix else key)
    }


async def test_english_translations_match_strings():
    """Test translations/en.json is a verbatim copy of strings.json."""
    assert _load("strings.json") == _load("translations/en.json")


async def test_every_translation_covers_all_keys():
    """Test each translation file defines exactly the keys strings.json declares.

    A missing key silently falls back to English, and a stale extra key hides a
    string that was renamed or removed.
    """
    expected = _key_paths(_load("strings.json"))

    for path in sorted((COMPONENT_DIR / "translations").glob("*.json")):
        actual = _key_paths(_load(f"translations/{path.name}"))

        assert not expected - actual, (
            f"{path.name} is missing: {sorted(expected - actual)}"
        )
        assert not actual - expected, (
            f"{path.name} has keys not in strings.json: {sorted(actual - expected)}"
        )


async def test_icons_reference_known_translation_keys(hass):
    """Test icons.json only names translation keys that actually exist.

    An icon under an unknown key is silently ignored by Home Assistant, so a
    typo would leave the entity on its generic fallback icon.
    """
    icons = _load("icons.json")["entity"]
    known = {
        platform: {entity.translation_key for entity in entities}
        for platform, entities in _entities(hass).items()
    }

    for platform, entries in icons.items():
        for key in entries:
            assert key in known[platform], (
                f"icons.json defines an icon for {platform} '{key}', but no such "
                "entity exists"
            )
