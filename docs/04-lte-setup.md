# LTE primary uplink

LTE is the **primary internet connection** when the drone is in flight — Wi-Fi is the bench/setup network. The Pi tethers through a Huawei HiLink-style dongle on `usb0`; outbound traffic (including the ZeroTier tunnel that carries MAVLink and video back to the GCS) goes over LTE.

## Hardware

See [02-hardware.md](02-hardware.md#lte-dongles) for supported dongles. tl;dr: anything with HiLink / CDC Ethernet out of the box. Huawei E3372-325 is proven.

## Physical install

1. **Pi Zero 2W:** the installer enables USB host mode (sets `dtoverlay=dwc2,dr_mode=host` and removes `g_ether` from `cmdline.txt`). A reboot is required; the installer tells you. After reboot, plug the dongle into the **middle** micro-USB port (labeled `USB`, not `PWR`) via an OTG adapter.
2. **Pi 4B / Pi 5:** no config needed, just plug the dongle into any USB-A port.

Power: the Pi's 5 V rail must handle the dongle's current (up to 500 mA in burst). If the Pi browns out when the dongle connects to cell, add a powered USB hub.

## Verifying detection

Open the **LTE** page in the web UI:
- If it says "No HiLink modem detected at 192.168.8.1" — the dongle isn't recognized. Check:
  - `ssh pi@drone.local 'lsusb'` — do you see the vendor entry?
  - `ssh pi@drone.local 'ip -br addr'` — is `usb0` present?
  - `ssh pi@drone.local 'dmesg | tail -30'` — any errors?
- If it shows status, signal, and connection code 901 — you're connected.

## SIM and APN

HiLink modems handle APN themselves — no config needed from the Pi side if the SIM has a data plan and the carrier has been visited before.

If the modem is flashing "no service" even with full signal:
- Open `http://192.168.8.1/` directly in a browser on the same LAN (the modem has its own web UI). Check the APN there; some SIMs require a specific APN that's not autoselected.
- Roaming: if it's an out-of-country SIM, data roaming must be enabled both on the SIM's plan and via the dongle's web UI.

## Testing LTE-only behaviour (forcing all traffic over LTE)

If you want to simulate "drone has flown out of Wi-Fi range", the safe way is:

```
sudo nmcli device disconnect wlan0
```

That brings Wi-Fi down for the rest of the current boot. **Reboot restores it** — the Wi-Fi profile's autoconnect is left intact, so even if LTE drops you can recover by power-cycling the Pi.

To restore Wi-Fi without reboot:

```
sudo nmcli connection up preconfigured
```

> **Don't** use `nmcli connection modify preconfigured connection.autoconnect no` for this test. That setting persists across reboots and will leave you locked out if LTE signal drops while you're remote. If you've already done it, the recovery is to either wait for LTE to recover and SSH back in, or pull the SD card and edit `/etc/NetworkManager/system-connections/preconfigured.nmconnection` to set `autoconnect=true`.

## Routing priority

The installer sets a NetworkManager profile on `usb0` with `ipv4.route-metric=800` — higher than `wlan0`'s default (600). This means **on the bench**, with both connected, Wi-Fi wins (faster, no carrier latency). **In flight**, with no Wi-Fi reachable, LTE is the only path so it wins by default.

To **prefer LTE even when Wi-Fi is up** (recommended for actual flight ops once the drone has left the workshop):
```
sudo nmcli connection modify drone-lte ipv4.route-metric 400
```

After that, `usb0` is the primary outbound interface whenever the dongle has signal.

## Signal quality thresholds

| Metric | Good | Marginal | Useless |
|---|---|---|---|
| RSRP | > -100 dBm | -100 to -115 dBm | < -115 dBm |
| RSRQ | > -12 dB | -12 to -18 dB | < -18 dB |
| SINR | > 10 dB | 0 to 10 dB | < 0 dB |

If you're stuck on useless: the dongle is physically in the wrong place. Co-located Wi-Fi radio on the same Pi desenses LTE badly. Move the dongle via USB extension cable, or add a dual-TS9 antenna.

## Known gotcha: old/dead SIM

If `workmode` shows `NO SERVICE` and signal looks fine (-75 dBm RSSI, for example) but RSRP is -115 dBm:
- Try the SIM in a phone to confirm it can register at all.
- If the SIM is expired or deactivated, the carrier's cells reject the registration request even though you have signal.
