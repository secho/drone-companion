# drone-companion

One-command installer that turns a Raspberry Pi into a drone companion computer:
MAVLink routing from your flight controller to your ground station, live H.264
video, ZeroTier mesh networking for remote access, and optional LTE failover.
Plus a simple web UI so you never have to SSH in to change a setting.

Supports **Raspberry Pi Zero 2W**, **Pi 4B**, and **Pi 5**.

## Status

Beta — built & tested end-to-end on drone2 (Pi Zero 2W + MicoAir 743 + IMX708) on 2026-04-24.

## What it does

- **MAVLink routing** — flight controller UART (`/dev/serial0`) ↔ UDP `:14550` + TCP `:5760` via `mavlink-router`, so any ground station (QGroundControl, Mission Planner, MAVProxy) connects by IP.
- **Live H.264 video** — Pi camera → RTP/UDP → your ground station, tunable quality/latency from the web UI.
- **ZeroTier** — one-click join, reach your drone over the internet without port-forwarding.
- **LTE failover (optional)** — plug in a Huawei HiLink-style dongle, the Pi routes over cellular when Wi-Fi drops.
- **Web UI at `http://<your-pi>.local/`** — status dashboard, video presets, MAVLink endpoint editor, ZeroTier join, LTE signal, reboot.

## Quickstart

1. **Flash Raspberry Pi OS Lite (64-bit)** with [Pi Imager](https://www.raspberrypi.com/software/). In the pre-set dialog, set hostname (e.g. `drone`), enable SSH with your public key, and preconfigure Wi-Fi.
2. **Boot the Pi and SSH in**:
   ```
   ssh <user>@<hostname>.local
   ```
3. **Run the installer** (this takes 5–10 min; longer on Pi Zero 2W because it builds mavlink-router from source):
   ```
   curl -fsSL https://raw.githubusercontent.com/<org>/drone-companion/main/install.sh | sudo bash
   ```
4. **If you're on a Pi Zero 2W**, reboot when prompted (the installer enables USB host mode for LTE support, which requires a reboot).
5. **Open `http://<hostname>.local/` in a browser** and walk through the 4-step setup wizard.
6. **Point your ground station** at the Pi — the Status page shows the exact connection strings to paste into QGC or Mission Planner.

See [`docs/01-quickstart.md`](docs/01-quickstart.md) for the fully-illustrated version.

## Documentation

- [`docs/01-quickstart.md`](docs/01-quickstart.md) — flash → install → fly, with screenshots
- [`docs/02-hardware.md`](docs/02-hardware.md) — supported Pi models, cameras, flight controllers, LTE dongles
- [`docs/03-gcs-setup.md`](docs/03-gcs-setup.md) — QGroundControl + Mission Planner settings
- [`docs/04-lte-setup.md`](docs/04-lte-setup.md) — SIM, APN, antenna tips
- [`docs/05-troubleshooting.md`](docs/05-troubleshooting.md) — the top 10 things that go wrong

## Upgrading

SSH into the Pi and run:
```
sudo drone-update
```

Your `/etc/drone/config.yaml` is never touched by upgrades.

## Uninstalling

```
sudo /opt/drone/uninstall.sh
```

(Leaves `/etc/drone/config.yaml` in place; delete manually if you want a truly clean slate.)

## Contributing

Issues and PRs welcome. Before opening a PR, please run:
```
# in ui/
pip install -e '.[dev]'
pytest
ruff check .

# at repo root
shellcheck install.sh installer/steps/*.sh scripts/*
bats installer/lib/*.bats scripts/*.bats
```

## License

MIT. See [LICENSE](LICENSE).
