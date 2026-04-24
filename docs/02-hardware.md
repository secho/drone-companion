# Supported hardware

## Raspberry Pi models

| Model | Status | Notes |
|---|---|---|
| Pi Zero 2W | ✅ tested | 2.4 GHz Wi-Fi only. Installer enables USB host mode → one reboot required. 512 MB RAM is tight but workable. |
| Pi 4B | ✅ tested | Better choice if LTE + video + MAVLink are all running. 5 GHz Wi-Fi for cleaner video. |
| Pi 5 | ✅ tested | Same config as Pi 4B. |
| Pi Zero W (1st gen) | ❌ | Too slow for mavlink-router build; single-core ARMv6. |
| Pi 3 / 3B+ | ⚠ untested | Should work; please report. |

## Cameras (CSI)

| Camera | Sensor | Notes |
|---|---|---|
| Camera Module 3 / 3 Wide | IMX708 | ✅ tested. Native autofocus works out of box. |
| Camera Module 3 Telephoto | IMX708 | Should work. |
| HQ Camera | IMX477 | Should work; manual lens choice. |
| Arducam 16MP IMX519 | IMX519 | ⚠ needs Arducam's patched libcamera (not upstream). Run their install script; see [05-troubleshooting.md](05-troubleshooting.md#arducam-imx519-no-autofocus). |
| Camera Module 2 | IMX219 | Works, but no autofocus (fixed-focus lens). |

### CSI ribbon orientation on Pi Zero 2W

Pi Zero 2W's CSI port uses a **narrower** ribbon than full-size Pis. Most kits ship with the adapter ribbon, but the orientation can be backwards. If `rpicam-hello --list-cameras` shows nothing and `dmesg` has `imx... probe ... failed with error -5`, **flip the ribbon 180°** at the Pi end.

## Flight controllers

Any ArduPilot- or PX4-based flight controller with a spare UART works. We've tested:

| FC | Firmware | UART | Notes |
|---|---|---|---|
| MicoAir 743 | ArduPilot 4.5+ | TELEM2 (labeled "UART4") | SERIAL4_PROTOCOL=2, SERIAL4_BAUD=115. The PCB silkscreen "UART4" maps to ArduPilot `SERIAL4` on this board, not SERIAL3 (which is GPS on the 743). |

Connect the FC's TELEM pins to the Pi's GPIO:

```
Pi GPIO 14 (TX) → FC UART RX
Pi GPIO 15 (RX) ← FC UART TX
Pi GND          ↔ FC GND
(do NOT cross-wire the 5V unless the FC expects it)
```

The installer assumes the FC is on `/dev/serial0` at 115200 baud. Change in the web UI's MAVLink page if different.

## LTE dongles

| Dongle | Mode | Status |
|---|---|---|
| Huawei E3372-325 (E3372h family) | HiLink (CDC Ethernet) | ✅ tested |
| Huawei E3372-320 | HiLink | Should work |
| Huawei E8372 (Wi-Fi hotspot) | HiLink | Should work for USB-tethering |
| Any modem exposing NDIS/CDC-ECM out of the box | — | Likely works |
| Sierra / Quectel / ZTE QMI-only modems | — | Needs more work; ModemManager config beyond v1 scope |

**HiLink modems** ("LTE sticks" sold for home use) are the easiest: they handle the LTE connection internally and present themselves as a USB Ethernet device with DHCP. The Pi just picks up an IP on `usb0` and routes out through it.

### Pi Zero 2W LTE wiring

The Zero 2W has **two micro-USB ports**. The middle one labeled `USB` is the data port (OTG-capable). The other labeled `PWR` is power-only. Plug the LTE dongle into the **USB** port via a micro-USB OTG adapter cable.

You'll also need:
- Power source for the Pi (on PWR port) OR a powered USB hub between dongle and Pi if the Pi's voltage regulator is marginal.
- The installer switches the Pi's USB to host mode. This requires a reboot — the installer prompts you.

### Antenna tips

Cheap LTE dongles have internal antennas. Performance indoors is often poor. For any serious deployment:
- Use a dongle with **external TS-9 antenna ports** (Huawei E3372-325 has them under the cover).
- Route the dongle on a USB extension cable **away from the Pi's Wi-Fi radio** — co-located 2.4 GHz Wi-Fi desenses the LTE front-end by 5–10 dB.
- Check signal on the LTE page: target RSRP > -100 dBm, SINR > 0 dB. Below -115 dBm you won't register.

## Ground station

Anything that speaks MAVLink over TCP or UDP. Tested:

- **QGroundControl** — use v4.4.x or a self-built v5 on macOS if you want video. The official v5 macOS DMG ships without GStreamer.
- **Mission Planner** (Windows) — works out of box.
- **MAVProxy** — `mavproxy.py --master=tcp:drone.local:5760`.
