# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-10-03

### Added

- **Liquid** option to count withdrawal and inflow of heating oil or other liquids as plain volume instead of water.

### Changed

- Buttons no longer request an update when they are added, which had no effect.
- **Breaking:** the Uptime sensor is replaced by **Last boot**, the time the device last started. Update automations and dashboards that use `sensor.<name>_uptime`.
- CI calls the shared workflows in josa42/actions, where they moved from josa42/gha-workflows.
- `make release` starts the release workflow: a minor version when a `feat` commit landed since the last release, a patch otherwise. Pass `VERSION=major`, `VERSION=minor`, `VERSION=patch` or `VERSION=1.2.3` to choose yourself. It refuses to start while local changes are not pushed.

### Fixed

- Spaces around the host entered during setup no longer break the connection to the device.
- Sensors no longer all become unavailable when the device reports an empty section.
- Pressing a button while the device is unreachable now shows a clear error instead of an unexpected one.
- The `start_measure` and `restart` actions now refuse a device whose integration is not loaded.
- Start measurement (button, action and device action) now waits for the new reading instead of showing the previous one, and fails if none arrives within 60 seconds.

[Unreleased]: https://github.com/josa42/homeassistant-liquid-check/compare/v1.2.0...HEAD
