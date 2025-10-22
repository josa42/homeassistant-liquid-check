# Home Assistant Liquid Check Integration

A custom integration for Home Assistant to check liquid levels.

## Installation

1. Copy the `custom_components/liquid_check` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI: Settings → Devices & Services → Add Integration → Liquid Check

## Configuration

Configure the integration through the Home Assistant UI.

## Development

This integration follows the [Home Assistant development guidelines](https://developers.home-assistant.io/docs/creating_component_index).

### Quick Local Testing

Test the integration in a local Home Assistant instance using Docker:

```bash
# Start Home Assistant with the integration
docker-compose up -d

# Open http://localhost:8123 and add the integration
# Device & Services → Add Integration → Liquid Check
```

See [DEV.md](DEV.md) for detailed development setup and troubleshooting.

### Running Tests

The project uses a virtual environment for dependency isolation.

Install dependencies (creates venv automatically):
```bash
make install
```

Run tests:
```bash
make test
```

### Linting

Run linter:
```bash
make lint
```

### Manual Setup

If you prefer to manage the virtual environment manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_test.txt
pip install ruff
pytest tests/ -v
```
