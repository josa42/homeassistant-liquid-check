# Home Assistant Liquid Check Integration

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A Home Assistant integration for monitoring Liquid Check devices. Track liquid levels, pump statistics, WiFi signal strength, and control your device remotely.

## Features

- 🌊 **Liquid Level Monitoring** - Real-time liquid level and temperature measurements
- 📊 **Pump Statistics** - Track total runs, runtime, and pump age
- 📡 **WiFi Signal** - Monitor device connectivity (RSSI)
- ⏱️ **Uptime Tracking** - Device and measurement age monitoring
- 🔧 **Remote Control** - Trigger measurements and restart device
- 🔄 **Configurable Updates** - Set custom polling intervals (default: 60s)
- 📱 **Full Device Support** - Shows up in Home Assistant devices tab

## Installation

### HACS (Recommended)

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add this repository URL: `https://github.com/josa42/homeassistant-liquid-check`
   - Select category: "Integration"
   - Click "Add"

2. **Install Integration**:
   - Go to HACS → Integrations
   - Click "+ Explore & Download Repositories"
   - Search for "Liquid Check"
   - Click "Download"
   - Restart Home Assistant

3. **Configure**:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Liquid Check"
   - Enter your device name and IP address
   - Optionally configure polling interval

### Manual Installation

1. Copy the `custom_components/liquid_check` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the integration through Settings → Devices & Services → Add Integration → Liquid Check

## Configuration

The integration is configured through the Home Assistant UI:

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**Liquid Check**"
3. Enter:
   - **Name**: Friendly name for your device (e.g., "Water Tank")
   - **IP Address**: Device IP address (e.g., 192.168.1.100)
   - **Scan Interval**: How often to poll the device in seconds (default: 60)

## Sensors

The integration provides 10 sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| **Liquid Level** | Current liquid level | % |
| **Temperature** | Liquid temperature | °C |
| **Level** | Measurement value | m |
| **WiFi RSSI** | WiFi signal strength | dBm |
| **Pump Total Runs** | Lifetime pump cycles | - |
| **Pump Total Runtime** | Lifetime pump operation time | min |
| **Uptime** | Device uptime | s |
| **Error** | Device error status | - |
| **Firmware** | Firmware version | - |
| **Measurement Age** | Time since last measurement | s |

## Services

### Start Measurement

Trigger a new measurement on the device.

```yaml
service: liquid_check.start_measure
target:
  device_id: your_device_id
```

### Restart Device

Restart the Liquid Check device remotely.

```yaml
service: liquid_check.restart
target:
  device_id: your_device_id
```

## Example Automations

### Low Liquid Level Alert

```yaml
automation:
  - alias: "Low Liquid Level Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.water_tank_liquid_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          message: "Water tank level is below 20%!"
```

### Daily Measurement Trigger

```yaml
automation:
  - alias: "Daily Tank Measurement"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: liquid_check.start_measure
        target:
          device_id: your_device_id
```

### Weekly Device Restart

```yaml
automation:
  - alias: "Weekly Device Restart"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: liquid_check.restart
        target:
          device_id: your_device_id
```

## Troubleshooting

**Integration not showing in Add Integration:**
- Restart Home Assistant after installation
- Check that files are in `config/custom_components/liquid_check/`
- Check Home Assistant logs for errors

**Cannot connect to device:**
- Verify the IP address is correct
- Ensure device is on the same network
- Check firewall settings

**Sensors show unavailable:**
- Check device is powered on and connected
- Verify IP address hasn't changed
- Check Home Assistant logs for connection errors

**Need more help?**
- Check [DEV.md](DEV.md) for development setup
- Open an [issue](https://github.com/josa42/homeassistant-liquid-check/issues)

## Development

See [DEV.md](DEV.md) for development setup, testing, and contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[releases-shield]: https://img.shields.io/github/release/josa42/homeassistant-liquid-check.svg
[releases]: https://github.com/josa42/homeassistant-liquid-check/releases
[license-shield]: https://img.shields.io/github/license/josa42/homeassistant-liquid-check.svg
