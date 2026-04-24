# Quickstart — from zero to flying in 15 minutes

This is the full, illustrated version of the steps in the README. Target audience: someone who has never set up a Raspberry Pi.

---

## What you need before you start

- A **Raspberry Pi** — Zero 2W, 4B, or 5.
- An **SD card** (8 GB+ recommended).
- A **Pi camera** connected via CSI ribbon. Supported: Camera Module 3 / 3 Wide, HQ Camera (IMX477), Arducam IMX519.
- A **flight controller** wired to the Pi's UART pins (`GPIO 14 TX` → FC RX, `GPIO 15 RX` ← FC TX, GND ↔ GND). Tested with ArduPilot on MicoAir 743.
- A **ground station** computer running QGroundControl or Mission Planner.
- A Wi-Fi network both the Pi and the ground station can see. (Or just use ZeroTier after install.)

## Step 1 — Flash Raspberry Pi OS Lite

Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/) and launch it.

Choose:
- **Device** — your model (Pi Zero 2W / 4B / 5)
- **OS** — *Raspberry Pi OS (other) → Raspberry Pi OS Lite (64-bit)*. "Lite" means no desktop; we don't need one.
- **Storage** — your SD card.

Before clicking **Write**, click the **gear icon** to open presets and fill in:
- Hostname: `drone` (so `drone.local` works)
- Enable SSH — paste your SSH public key (or set password auth if you must)
- Configure wireless LAN: your Wi-Fi SSID + password + country
- Set locale

Hit **Save**, then **Write**. Takes ~3 minutes.

## Step 2 — Boot and SSH in

Insert the SD card, power on the Pi. First boot takes ~90 seconds as it resizes the filesystem.

From your laptop:

```
ssh <your-user>@drone.local
```

The first connection will ask you to confirm the host key — type `yes`.

## Step 3 — Run the installer

```
curl -fsSL https://raw.githubusercontent.com/<org>/drone-companion/main/install.sh | sudo bash
```

What this does:
- Installs GStreamer, `mavlink-router` (builds from source), ZeroTier, Avahi, NetworkManager.
- Creates a `drone` system user and `/opt/drone/`.
- Drops three systemd services (`drone-ui`, `drone-video`, `mavlink-router`).
- On Pi Zero 2W: enables USB host mode for LTE (requires a reboot after install).

Expect 5 minutes on Pi 4B / Pi 5, 10–20 minutes on Pi Zero 2W (it builds mavlink-router from source, which is slow on the Zero's 4×A53 cores).

When it's done, you'll see:

```
[OK] Done.

Open http://drone.local/ in a browser on the same network to configure your drone.
```

**If the installer told you to reboot** (Pi Zero 2W only):
```
sudo reboot
```
Wait ~90 seconds, then continue.

## Step 4 — Open the web UI

Point your browser at `http://drone.local/` (or whatever hostname you chose).

First time you visit, you'll land on the **setup wizard**:

1. **GCS host** — your ground station's IP address. Look it up on your GCS machine:
   - macOS/Linux: `ifconfig | grep inet`
   - Windows: `ipconfig` in CMD

2. **Video quality preset**:
   - `480p20_600K` — most reliable over 2.4 GHz Wi-Fi
   - `720p30_3M` — looks great on Pi 4B/5 over 5 GHz Wi-Fi
   - `1080p30_6M` — requires very clean Wi-Fi; expect artifacts over ZeroTier on cheap routers

3. **ZeroTier (optional)** — paste a network ID from [my.zerotier.com](https://my.zerotier.com) if you want to reach the drone from anywhere. Leave blank to skip; you can do it later.

4. **Summary** — review and click **Save and start**. The Pi starts streaming video and MAVLink.

## Step 5 — Connect your ground station

See [03-gcs-setup.md](03-gcs-setup.md) for screenshots. Short version:

**QGroundControl:**
- Application Settings → Comm Links → Add
- Type: **TCP**
- Host: `drone.local` (or the Pi's IP)
- Port: `5760`
- Save, then Connect.

For video:
- Application Settings → Video → Source: **UDP h.264 Video Stream**, Port: `5600`.
- Open the Fly view — video appears in the PiP window within ~2 seconds.

**Mission Planner:**
- Connect dropdown (top-right) → **TCP**
- Enter `drone.local` and port `5760`.

## Step 6 — Fly

You should now have:
- MAVLink telemetry streaming from the flight controller, through the Pi, to your GCS.
- Live H.264 video from the Pi camera, rendered in the Fly view.

Changes to video quality, GCS address, etc. are applied live from the web UI — no SSH needed.

---

## Common first-run issues

See [05-troubleshooting.md](05-troubleshooting.md). The usual suspects:

- **`drone.local` doesn't resolve on Windows** → install [Bonjour Print Services](https://support.apple.com/kb/DL999) or use the Pi's IP directly.
- **Video Source dropdown has no UDP option in QGC** → you have the official v5.x macOS DMG which ships without GStreamer. Either downgrade to v4.4.x, build v5 from source, or use `ffplay` with an SDP file.
- **"Access denied" when Pi tries to read the FC UART** → the installer adds `drone` to the `dialout` group; log out and back in, or reboot.
