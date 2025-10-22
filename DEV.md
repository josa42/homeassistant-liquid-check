# Development Setup

## Quick Start with Docker

This setup allows you to test the integration in a local Home Assistant instance.

### Prerequisites
- Docker and Docker Compose installed
- The Liquid Check device accessible on your network (e.g., 10.0.0.47)

### Start Home Assistant

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

### Useful Commands

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
```

### Troubleshooting

**Integration not showing up:**
- Check the custom_components folder is mounted correctly
- Look for errors in logs: `docker-compose logs homeassistant | grep liquid`
- Restart Home Assistant: `docker-compose restart`

**Cannot connect to device:**
- Verify device IP address is correct
- Ensure device is accessible from Docker container
- Test connection: `docker-compose exec homeassistant curl http://10.0.0.47/infos.json`

**Configuration changes not reflected:**
- Always restart Home Assistant after code changes
- Clear browser cache if UI doesn't update

### Testing with Mock Data

If you don't have a physical device, you can mock the endpoint:

```bash
# Run a simple mock server (requires Python)
python3 -m http.server 8080 --directory tests/fixtures/
```

Then configure the integration to use `localhost:8080` as the IP.

### Integration Logs

To see detailed logs from your integration, add to `config/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.liquid_check: debug
```

Then restart Home Assistant.
