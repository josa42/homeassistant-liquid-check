# Development Guide

This guide covers development setup, testing, and contribution guidelines for the Liquid Check integration.

## Development Setup

### Prerequisites

- Python 3.12 or later
- Git
- Docker and Docker Compose (for local testing)
- A Liquid Check device (or mock server)

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/josa42/homeassistant-liquid-check.git
   cd homeassistant-liquid-check
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```
   This creates a virtual environment and installs all test dependencies.

3. **Run tests**:
   ```bash
   make test
   ```

4. **Run linter**:
   ```bash
   make lint
   ```

### Manual Virtual Environment Setup

If you prefer manual control:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_test.txt
pip install ruff
```

## Testing

### Unit Tests

Run all tests:
```bash
make test
```

Run specific test file:
```bash
venv/bin/python -m pytest tests/test_sensor.py -v
```

Run specific test:
```bash
venv/bin/python -m pytest tests/test_sensor.py::test_sensor_setup -v
```

### Code Coverage

```bash
venv/bin/python -m pytest tests/ --cov=custom_components/liquid_check --cov-report=html
open htmlcov/index.html
```

### Linting

The project uses Ruff for linting:

```bash
make lint
```

Fix auto-fixable issues:
```bash
venv/bin/ruff check --fix custom_components/ tests/
```

## Local Testing with Docker

Test the integration in a real Home Assistant instance.

### Quick Start

```bash
# Start Home Assistant
docker-compose up -d

# Follow logs
docker-compose logs -f

# Stop Home Assistant
docker-compose down
```

### First Run Setup

1. **Wait for Home Assistant to start** (takes 1-2 minutes on first run)
2. **Open browser**: http://localhost:8123
3. **Complete onboarding**: Create admin account
4. **Add the integration**:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Liquid Check"
   - Enter your device name and IP address

### Development Workflow

1. **Make changes** to the integration code in `custom_components/liquid_check/`
2. **Restart Home Assistant**:
   ```bash
   docker-compose restart
   ```
3. **Check logs** for errors:
   ```bash
   docker-compose logs -f homeassistant
   ```
4. **Or restart from Developer Tools** in Home Assistant UI

### Useful Docker Commands

```bash
# View Home Assistant logs
docker-compose logs -f

# Restart after code changes
docker-compose restart

# Full reset (deletes config)
docker-compose down -v
rm -rf config/*
docker-compose up -d

# Enter container shell
docker-compose exec homeassistant bash

# Check integration is loaded
docker-compose exec homeassistant ls -la /config/custom_components/

# Test device connection
docker-compose exec homeassistant curl http://10.0.0.47/infos.json
```

### Enable Debug Logging

Add to `config/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.liquid_check: debug
```

Then restart Home Assistant.

## Testing with Mock Data

If you don't have a physical device:

### Option 1: Mock HTTP Server

Create a simple mock server:

```python
# mock_server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/infos.json':
            data = {
                "level": 75.5,
                "temp": 22.3,
                "raw": 120,
                "rssi": -65,
                "totalRuns": 1234,
                "totalRuntime": 5678,
                "uptime": 86400,
                "error": 0,
                "firmware": "1.2.3",
                "age": 300
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/command':
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

HTTPServer(('', 8080), MockHandler).serve_forever()
```

Run it:
```bash
python3 mock_server.py
```

Configure integration to use `localhost:8080`.

### Option 2: pytest-respx

Tests use `pytest-respx` to mock HTTP requests. See `tests/test_sensor.py` for examples.

## Project Structure

```
homeassistant-liquid-check/
├── custom_components/liquid_check/   # Integration code
│   ├── __init__.py                   # Setup entry, services
│   ├── config_flow.py                # Config flow UI
│   ├── const.py                      # Constants
│   ├── coordinator.py                # Data update coordinator
│   ├── sensor.py                     # Sensor entities
│   ├── services.yaml                 # Service definitions
│   └── manifest.json                 # Integration metadata
├── tests/                            # Unit tests
│   ├── test_config_flow.py
│   ├── test_init.py
│   ├── test_sensor.py
│   └── test_services.py
├── config/                           # Docker test config
├── .github/workflows/                # CI/CD
├── docker-compose.yml                # Local testing
├── Makefile                          # Dev commands
├── pytest.ini                        # Pytest config
├── ruff.toml                         # Linter config
├── requirements_test.txt             # Test dependencies
├── DEV.md                            # This file
└── README.md                         # User documentation
```

## Contribution Guidelines

### Before Submitting

1. **Run tests**: `make test`
2. **Run linter**: `make lint`
3. **Test locally**: Use docker-compose to test changes
4. **Update docs**: Update README.md if adding features

### Commit Messages

Use conventional commits:

```
feat: add restart device service
fix: handle connection timeout errors
docs: update installation instructions
test: add tests for coordinator
chore: update dependencies
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and commit: `git commit -m "feat: add my feature"`
4. Push to your fork: `git push origin feature/my-feature`
5. Open a pull request

### Code Style

- Follow Home Assistant coding standards
- Use type hints
- Add docstrings to public functions
- Keep functions small and focused
- Write tests for new features

## Troubleshooting

### Integration not showing up in Docker

- Check the custom_components folder is mounted correctly
- Look for errors in logs: `docker-compose logs homeassistant | grep liquid`
- Restart Home Assistant: `docker-compose restart`

### Cannot connect to device from Docker

- Verify device IP address is correct
- Ensure device is accessible from Docker container
- Test connection: `docker-compose exec homeassistant curl http://10.0.0.47/infos.json`
- On macOS, use `host.docker.internal` instead of `localhost`

### Configuration changes not reflected

- Always restart Home Assistant after code changes
- Clear browser cache if UI doesn't update
- Check Developer Tools → Logs for errors

### Tests failing

- Ensure virtual environment is activated
- Update dependencies: `pip install -r requirements_test.txt`
- Check Python version: `python --version` (needs 3.12+)

### Import errors in tests

- Install the package in development mode: `pip install -e .`
- Or run tests from the repository root

## CI/CD

The project uses GitHub Actions for:

- **Linting**: Ruff checks on every push
- **Testing**: Pytest on Python 3.12
- **Validation**: HACS validation

See `.github/workflows/ci.yml` for details.

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Development](https://developers.home-assistant.io/docs/creating_component_index)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index)
- [HACS Documentation](https://hacs.xyz/docs/publish/start)

## Getting Help

- Open an [issue](https://github.com/josa42/homeassistant-liquid-check/issues) for bugs
- Start a [discussion](https://github.com/josa42/homeassistant-liquid-check/discussions) for questions
- Check existing issues before creating new ones
