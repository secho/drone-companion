# Drone Companion Computer

**One-command setup for a Raspberry Pi-based drone companion computer.** Routes MAVLink from your flight controller to any ground station, streams live H.264 video from the Pi camera, joins a ZeroTier mesh so the drone is reachable over the internet, and tethers through an LTE dongle as the **primary internet uplink**. A simple web UI replaces SSH for everyday config.

Supported hardware: **Raspberry Pi Zero 2W**, **Pi 4B**, **Pi 5**.

## Status

Beta — built and tested end-to-end on a Pi Zero 2W with a MicoAir 743 (ArduPilot) and an IMX708 camera, 2026-04-24.

---

## Architecture

```
                          ┌──────────────────────────────────────────────────┐
                          │  Raspberry Pi   (drone companion computer)       │
                          │                                                  │
       Flight Controller ─┤UART──► mavlink-router ──► UDP :14550 ┐           │
       (ArduPilot/PX4)    │                       └──► TCP :5760 ┤           │
                          │                                      │           │
       Pi Camera ─────────┤CSI──► rpicam-vid ──► H.264 ──► RTP/UDP ──────┐  │
       (IMX708, IMX519,   │                                      │       │  │
        IMX477, …)        │                                      │       │  │
                          │   /etc/drone/config.yaml ◄──┐        │       │  │
                          │      (single source of truth)│        │       │  │
                          │                              │        │       │  │
                          │   drone-ui ◄─────────────────┘ writes │       │  │
                          │   (FastAPI + HTMX, port 80)           │       │  │
                          │                                       │       │  │
                          │   zerotier-one (mesh VPN)             │       │  │
                          │                                       │       │  │
                          └────────────┬───────────────────┬──────┴───────┴──┘
                                       │                   │
                          ┌────────────▼─┐         ┌───────▼────────────┐
                          │  Wi-Fi (LAN) │         │  LTE dongle (USB)  │
                          │  wlan0       │         │  HiLink → usb0     │
                          │  (optional)  │         │  (primary uplink)  │
                          └──────────┬───┘         └─────────┬──────────┘
                                     │                       │
                                     └───────┬───────────────┘
                                             │
                                       ┌─────▼──────┐
                                       │  Internet  │
                                       └─────┬──────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │  ZeroTier root nodes │
                                  └──────────┬───────────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │    Ground Station    │
                                  │  QGroundControl /    │
                                  │   Mission Planner    │
                                  └──────────────────────┘
```

The web UI reads and writes a single YAML at `/etc/drone/config.yaml`. A `reload-config` script renders that YAML into the downstream service configs (`/etc/default/drone-video`, `/etc/mavlink-router/main.conf`) via Jinja templates and restarts only the affected services. If a new config breaks a service on start, the previous-known-good is rolled back automatically.

---

## What it does

- **MAVLink routing** — flight controller UART (`/dev/serial0`) ↔ UDP `:14550` and TCP `:5760` via `mavlink-router`. Any GCS connects by IP.
- **Live H.264 video** — Pi camera → RTP/UDP → your ground station. Quality presets live in the web UI.
- **ZeroTier mesh** — one-click join. Your laptop and the drone get private virtual IPs and reach each other over the internet without port-forwarding.
- **LTE primary uplink** — plug in a Huawei HiLink dongle (or compatible). The Pi tethers through it for outbound internet (which is how ZeroTier reaches the drone in the field). Wi-Fi is the bench/setup network; in flight it's LTE.
- **Web UI** at `http://<your-pi>.local/` — status dashboard, video presets, MAVLink endpoints, ZeroTier join, LTE signal, reboot, diagnostics bundle download.

---

## Wiring: flight controller to Raspberry Pi

The Pi reads MAVLink from the flight controller via a 3-wire UART connection: TX, RX, GND.

### Pi GPIO header

```
         3V3  (1) (2)  5V         ─── Don't usually power FC from Pi
       GPIO2  (3) (4)  5V         (the FC has its own BEC; share GND only)
       GPIO3  (5) (6)  GND ◄────────┐
       GPIO4  (7) (8)  GPIO14 (TX) ─┤  ◄── connects to FC RX
         GND  (9)(10)  GPIO15 (RX) ─┤  ◄── connects to FC TX
                                    │
                                    └─── these three lines are the link
```

### Connection table

| Pi pin (BCM) | Pi physical pin | ↔ | Flight controller |
|---:|:---:|:---:|:---|
| **GPIO 14** (TX) | 8 | → | `RX` of a free FC UART |
| **GPIO 15** (RX) | 10 | ← | `TX` of the same FC UART |
| **GND** | 6, 9, 14, 20, 25, 30, 34, or 39 | ↔ | `GND` of the same FC UART |

```
                                Pi Zero 2W / Pi 4B / Pi 5 GPIO header
                                    (top-down view, looking at board)

                                       ┌───────────────────────────┐
                                pin 1 ─►●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ...
                                       ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ...
                                       └─┬──┬─────┬──┬───────────────┘
                                         │  │     │  │
                                         │  │     │  └── pin 10  GPIO 15 (RX) ◄── FC TX
                                         │  │     └───── pin 8   GPIO 14 (TX) ──► FC RX
                                         │  └─────────── pin 6   GND          ◄─► FC GND
                                         └────────────── pin 4   5V (don't use)
```

### ArduPilot FC parameters (typical)

Pick a free UART on your FC. Example for ArduPilot using `SERIAL4`:

```
SERIAL4_PROTOCOL = 2     # MAVLink 2
SERIAL4_BAUD     = 115   # 115200 baud (ArduPilot baud code, not literal rate)
BRD_SER4_RTSCTS  = 0     # no flow control on a 3-wire link
```

Reboot the FC after changing — `SERIAL*` params apply at boot only.

> **Don't power the FC from the Pi's 5 V pin.** Modern FCs have their own BEC fed from the battery and are designed to be powered that way. Connect TX, RX, and GND only. Cross-feeding 5 V can damage the Pi's regulator or back-feed into the FC.

> **MicoAir 743 specifically:** the silkscreen-labeled "UART4" maps to ArduPilot `SERIAL4` on this board, *not* `SERIAL3` (which is the GPS port). Confirmed by hardware test, not by hwdef guesses.

> **Logic levels:** Pi GPIO is 3.3 V. Most modern FCs (any STM32-based ArduPilot/PX4 board from the last decade) speak 3.3 V on TELEM pads — direct connection is correct. If you're on something exotic with 5 V TTL, add a level shifter.

For more on hardware compatibility see [`docs/02-hardware.md`](docs/02-hardware.md).

---

## Quickstart

1. **Flash Raspberry Pi OS Lite (64-bit)** with [Pi Imager](https://www.raspberrypi.com/software/). In the pre-set dialog, set the hostname (e.g. `drone`), enable SSH with your public key, and preconfigure Wi-Fi (used for the initial setup).
2. **Boot the Pi and SSH in**:
   ```
   ssh <user>@<hostname>.local
   ```
3. **Run the installer** (5–10 min on Pi 4B/5, 15–25 min on Pi Zero 2W — it builds mavlink-router from source on the Pi):
   ```
   curl -fsSL https://raw.githubusercontent.com/secho/drone-companion/main/install.sh | sudo bash
   ```
4. **If on a Pi Zero 2W**, reboot when prompted — the installer enables USB host mode (`dwc2,dr_mode=host`) so LTE dongles enumerate. Pi 4B / Pi 5 already have host mode by default.
5. **Plug in the LTE dongle** (Huawei E3372 or compatible HiLink). The Pi will pick up DHCP from it on `usb0`.
6. **Open `http://<hostname>.local/` in a browser** and walk through the 4-step setup wizard:
   1. Tell the Pi your ground station's IP.
   2. Pick a video quality preset.
   3. Paste a ZeroTier network ID (optional but recommended for in-flight access).
   4. Confirm and start.
7. **Point your ground station** at the Pi. The status page shows the exact connection strings to paste into QGC or Mission Planner.

For the fully-illustrated step-by-step with screenshots, see [`docs/01-quickstart.md`](docs/01-quickstart.md).

---

## Documentation

- [`docs/01-quickstart.md`](docs/01-quickstart.md) — flash → install → fly, with screenshots
- [`docs/02-hardware.md`](docs/02-hardware.md) — supported Pis, cameras, flight controllers, LTE dongles
- [`docs/03-gcs-setup.md`](docs/03-gcs-setup.md) — QGroundControl + Mission Planner settings
- [`docs/04-lte-setup.md`](docs/04-lte-setup.md) — SIM, APN, antenna tips, signal thresholds
- [`docs/05-troubleshooting.md`](docs/05-troubleshooting.md) — the top 10 things that go wrong

---

## Upgrading

```
sudo drone-update
```

Pulls the latest `main`, re-runs the installer (idempotent — only changed steps execute). Your `/etc/drone/config.yaml` is never touched.

## Uninstalling

```
sudo /opt/drone/uninstall.sh
```

Leaves `/etc/drone/config.yaml` in place. Delete manually if you want a truly clean slate.

## Contributing

Issues and PRs welcome. Before opening a PR:

```
# Python tests
cd ui && pip install -e '.[dev]' && pytest

# Shell linters and tests
shellcheck install.sh installer/steps/*.sh scripts/*
bats installer/lib/*.bats scripts/*.bats
```

CI runs the same on every push.

## License

MIT. See [LICENSE](LICENSE).
