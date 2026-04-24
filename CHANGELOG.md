# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial installer with 9 idempotent steps (hardware detection, packages, users/dirs, ZeroTier, mavlink-router, camera/GStreamer, LTE/USB host mode, UI venv, systemd services).
- Web UI (FastAPI + HTMX) at port 80: status dashboard, video presets, MAVLink endpoints, ZeroTier join/leave, LTE HiLink status, system controls, 4-step first-run wizard.
- `/etc/drone/config.yaml` as single source of truth, pydantic-validated.
- `reload-config` script with automatic rollback on service-start failure.
- Bundled GStreamer pipeline tuned for low-bandwidth wireless links (no ULPFEC by default — QGC doesn't consume it).
- `drone-update` wrapper for in-place upgrades.
- MIT license.

### Hardware tested on
- Raspberry Pi Zero 2W + MicoAir 743 ArduPilot FC + IMX708 camera + Huawei E3372 HiLink LTE dongle.
