# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Liquid** option to count withdrawal and inflow of heating oil or other liquids as plain volume instead of water.

### Changed

- Buttons no longer request an update when they are added, which had no effect.
- **Breaking:** the Uptime sensor is replaced by **Last boot**, the time the device last started. Update automations and dashboards that use `sensor.<name>_uptime`.

### Fixed

- Spaces around the host entered during setup no longer break the connection to the device.
- Sensors no longer all become unavailable when the device reports an empty section.
- Pressing a button while the device is unreachable now shows a clear error instead of an unexpected one.
- The `start_measure` and `restart` actions now refuse a device whose integration is not loaded.

[Unreleased]: https://github.com/josa42/homeassistant-liquid-check/compare/v1.2.0...HEAD
