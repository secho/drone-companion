# Troubleshooting

If your problem isn't below, grab the diagnostics bundle from the **System** page of the web UI and attach it to a GitHub issue.

## Installer

### `curl: (22) … 404` during install

The `install.sh` URL in the README is a placeholder until you know where the repo lives. Use the actual GitHub org/repo from the repo you're using.

### `ModuleNotFoundError: drone_ui.config` during step 90

The venv wasn't populated. Check `/opt/drone/venv/bin/python -c 'import drone_ui'` — if it errors, re-run `sudo /opt/drone/installer/steps/80-ui.sh`.

### `visudo -c` rejects the sudoers file

Something in step 80 corrupted the drop-in. Safe to delete and re-run:
```
sudo rm /etc/sudoers.d/drone-ui
sudo /opt/drone/installer/steps/80-ui.sh
```

## Video

### "Waiting for video" forever in QGC

Most common cause: you have the official QGC v5 macOS DMG, which ships without GStreamer, so there's no decoder. The Source dropdown will literally only have "Video Stream Disabled." See [03-gcs-setup.md](03-gcs-setup.md#source-dropdown-only-shows-video-stream-disabled) for fixes.

### Green macroblock artifacts

Classic packet loss. Every lost H.264 packet garbles 16×16 pixel blocks. Fixes:
- Drop to a lower preset in the web UI (`480p20_600K`).
- Move the drone closer to the AP, or use 5 GHz on Pi 4B/5.
- On Pi Zero 2W (2.4 GHz only): you're fundamentally limited to ~1 Mbps of clean H.264 on typical home networks. Drop the bitrate.

### VideoToolbox decoder errors on macOS

If the QGC/`gst-launch` log shows `vtdechw` errors on every frame:
```
GST_PLUGIN_FEATURE_RANK='vtdec:NONE,vtdec_hw:NONE,vtdech264:NONE' /Applications/QGroundControl.app/Contents/MacOS/QGroundControl
```
This disables Apple's VideoToolbox hardware decoder and forces ffmpeg software decoding (which is reliable but uses more CPU).

### Arducam IMX519: no autofocus

Upstream Raspberry Pi libcamera doesn't ship an AF tuning for IMX519. Install Arducam's patched libcamera:
```
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
```
Also edit `/boot/firmware/config.txt`: replace `dtoverlay=imx708` with `dtoverlay=imx519`.

### `rpicam-hello --list-cameras` shows nothing

Check `dmesg | grep -iE "imx|unicam"` for `probe with driver ... failed with error -5`. That's the fingerprint of reversed CSI ribbon orientation on a Pi Zero 2W adapter. Flip the ribbon 180° at one end and reboot.

## MAVLink

### No heartbeats reach QGC

Most likely: the FC isn't sending on the UART you configured. Quick test on the Pi:
```
sudo systemctl stop mavlink-router
sudo stty -F /dev/serial0 115200 raw -echo
timeout 3 sudo dd if=/dev/serial0 of=/tmp/u.bin bs=1 count=32768 2>/dev/null
python3 -c 'd=open("/tmp/u.bin","rb").read(); print(len(d),"bytes, v2=",d.count(bytes([0xfd])))'
```

- 0 bytes → UART is silent. Check FC's `SERIAL*_PROTOCOL` and `SERIAL*_BAUD`; make sure you rebooted the FC after changing them.
- Noise that scales with baud → floating RX line, FC not transmitting.
- Proper `0xfd`-prefixed frames → UART is fine; issue is in mavlink-router or downstream. Restart: `sudo systemctl start mavlink-router && journalctl -u mavlink-router -f`.

### `[Errno 13] Permission denied: '/dev/serial0'`

The `drone` user needs the `dialout` group. Installer handles this, but the session must be restarted after group changes:
```
sudo systemctl restart mavlink-router
```

### MicoAir 743: which UART?

On this specific board, the PCB silkscreen "UART4" maps to ArduPilot `SERIAL4`, **not** `SERIAL3` (which is the GPS on this board). Set:
```
SERIAL4_PROTOCOL = 2   (MAVLink 2)
SERIAL4_BAUD     = 115 (= 115200)
BRD_SER4_RTSCTS  = 0   (no flow control)
```
Reboot the FC after changing.

## ZeroTier

### "Node ID: (zerotier-one not running)"

```
sudo systemctl restart zerotier-one
sudo zerotier-cli info
```
Should print `200 info <node-id> <ver> ONLINE`.

### Joined network but no IP assigned

Go to [my.zerotier.com](https://my.zerotier.com) → your network → **Members** → check the box next to your Pi's node ID to authorize it. By default joins are unauthorized.

## LTE

See [04-lte-setup.md](04-lte-setup.md) for signal thresholds and antenna tips. Most LTE "it doesn't work" issues are physical (signal, SIM registration).

## Upgrade

### `drone-update` fails with "Not a git checkout at /opt/drone"

If you installed via the tarball path instead of `curl | bash`, there's no `.git` directory. Re-install via the canonical path:
```
sudo rm -rf /opt/drone
curl -fsSL https://raw.githubusercontent.com/secho/drone-companion/main/install.sh | sudo bash
```
