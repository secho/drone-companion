# Release QA checklist

Run this before tagging a release. Ideally on all three target Pi models.

## Pre-install

- [ ] Clone repo to a fresh SD card's Pi OS Lite 64-bit image via Pi Imager.
- [ ] Flash + boot + SSH in.
- [ ] Confirm `cat /proc/device-tree/model` reports the expected Pi model.

## Install

- [ ] `curl -fsSL https://raw.githubusercontent.com/secho/drone-companion/main/install.sh | sudo bash` exits 0.
- [ ] `/var/log/drone-install.log` has no `ERROR` lines.
- [ ] `ls /var/lib/drone/markers/` shows all 9 `*.done` markers.
- [ ] On Pi Zero 2W only: `/boot/firmware/cmdline.txt` no longer contains `g_ether`, and `/boot/firmware/config.txt` has `dtoverlay=dwc2,dr_mode=host` in `[all]`.

## Web UI

- [ ] `curl http://drone.local/healthz` returns `{"status":"ok"}`.
- [ ] `http://drone.local/` redirects to `/setup/1` on first run.
- [ ] Wizard completes end-to-end: gcs → video preset → skip ZT → summary → finish.
- [ ] After finish, `/` renders the status dashboard with service states.
- [ ] Changing a video preset on `/video` results in `systemctl status drone-video` showing the service restarted.
- [ ] `/system/diagnostics` downloads a non-zero `.tar.gz`.

## Services

- [ ] `systemctl is-active drone-ui` → `active`.
- [ ] `systemctl is-active drone-video` → `active`.
- [ ] `systemctl is-active mavlink-router` → `active`.
- [ ] `systemctl is-active zerotier-one` → `active`.

## End-to-end

- [ ] Connect QGC (TCP 5760) → MAVLink link comes up, vehicle data populates.
- [ ] Connect video (UDP 5600) → live frames render in Fly view.
- [ ] Reboot the Pi, re-verify all four services come up automatically.

## Upgrade

- [ ] Tag `vX.Y.Z` in git, push.
- [ ] SSH into drone, run `sudo drone-update`.
- [ ] Re-check `/healthz`, MAVLink, video.
- [ ] Confirm `/etc/drone/config.yaml` is unchanged after upgrade.

## Uninstall

- [ ] `sudo /opt/drone/uninstall.sh` removes services and `/opt/drone/`.
- [ ] `/etc/drone/config.yaml` remains in place (user's settings preserved).
