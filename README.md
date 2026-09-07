# Home Assistant Liquid Check Integration

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A Home Assistant integration to use the [Liquid-Check](https://liquid-check-info.si-elektronik.de/) sensor in Home Assistant. The Liquid-Check is a liquid level monitoring device manufactured by [SI-Elektronik GmbH](https://www.si-elektronik.de/).

> **Note:** This integration is not affiliated with or endorsed by SI-Elektronik GmbH. It is a community-developed project.

<br><br>

## Features

- 🌊 **Liquid Level Monitoring** - Real-time liquid level measurements in non-pressurized containers
- 📊 **Volume Tracking** - Monitor content in liters and percentage
- 🔌 **Pump Monitoring** - Track connected pump runs and runtime
- 📡 **WiFi Signal** - Monitor device connectivity (RSSI)
- ⏱️ **Uptime Tracking** - Device and measurement age monitoring
- 🔧 **Remote Control** - Trigger measurements and restart device
- 🔄 **Configurable Updates** - Set custom polling intervals (default: 60s, or disable automatic polling)
- 📱 **Full Device Support** - Shows up in Home Assistant devices tab
- 🌍 **Translations** - English and German

<br><br>

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

<br><br>

## Configuration

The integration is configured through the Home Assistant UI:

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**Liquid Check**"
3. Enter:
   - **Name**: Friendly name for your device (e.g., "Water Tank")
   - **IP Address**: Device IP address (e.g., 192.168.1.100)
   - **Scan Interval**: How often to poll the device in seconds (default: 60, set to 0 to disable automatic polling)

The scan interval can be changed later under **Settings** → **Devices & Services**
→ **Liquid Check** → **Configure**. If the device moves to a new IP address, add
it again with the new address and the existing device is updated in place.

<br><br>

## Sensors

The integration provides 10 sensors:

| Sensor | Description | Unit | Enabled by Default |
|--------|-------------|------|--------------------|
| **Level** | Liquid level distance | m | ✓ |
| **Content** | Liquid volume | L | ✓ |
| **Percent** | Fill level percentage | % | ✓ |
| **WiFi RSSI** | WiFi signal strength | dBm | |
| **Pump total runs** | Connected pump total cycles | - | |
| **Pump total runtime** | Connected pump total operation time | s | |
| **Uptime** | Device uptime | s | |
| **Error** | Device error status | - | |
| **Firmware** | Firmware version | - | |
| **Measurement age** | Time since last measurement | s | |

The seven sensors that are off by default are diagnostic. Enable the ones you
want under the device page. Firmware and hardware revision are also shown on the
device itself, so you only need the firmware sensor if you template against it.

<br><br>

## Services

Both services take the device ID of your Liquid Check. Pick the device from the
dropdown under **Developer Tools** → **Actions** and switch to YAML mode to see
the ID, or use the device actions on the automation editor's device page, which
fill it in for you.

### Start Measurement

Trigger a new measurement on the device.

```yaml
action: liquid_check.start_measure
data:
  device_id: 5d6b2f28d240e1bf33238cc013bb578c
```

### Restart Device

Restart the Liquid Check device remotely.

```yaml
action: liquid_check.restart
data:
  device_id: 5d6b2f28d240e1bf33238cc013bb578c
```

<br><br>

## Example Automations

### Low Liquid Level Alert

```yaml
automation:
  - alias: "Low Liquid Level Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.water_tank_percent
        below: 20
    action:
      - action: notify.mobile_app
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
      - action: liquid_check.start_measure
        data:
          device_id: 5d6b2f28d240e1bf33238cc013bb578c
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
      - action: liquid_check.restart
        data:
          device_id: 5d6b2f28d240e1bf33238cc013bb578c
```

<br><br>

## Development

See [DEV.md](DEV.md) for development setup, testing, and contribution guidelines.

<br><br>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[releases-shield]: https://img.shields.io/github/release/josa42/homeassistant-liquid-check.svg
[releases]: https://github.com/josa42/homeassistant-liquid-check/releases
[license-shield]: https://img.shields.io/github/license/josa42/homeassistant-liquid-check.svg
