#!/usr/bin/env bash
# 65-uart.sh — make /dev/serial0 a real, reliable UART for the flight controller.
#
# What this fixes:
#   * Pi OS Lite ships with `enable_uart=0` (no UART on GPIO14/15).
#   * Bluetooth on the Pi steals PL011, so `/dev/serial0` symlinks to the
#     mini-UART whose baud rate floats with CPU clock — unusable for MAVLink.
#   * `console=serial0,115200` in /boot/firmware/cmdline.txt makes the kernel
#     dump boot logs onto our UART and run a getty there, blocking mavlink-router.
#   * `serial-getty@ttyS0` / `serial-getty@ttyAMA0` services may still be enabled.
#   * `hciuart` keeps Bluetooth bound to PL011 across reboots.
#
# Idempotent. Requires reboot to take effect.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="65-uart"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

BOOT_CONFIG="${DRONE_BOOT_CONFIG:-/boot/firmware/config.txt}"
BOOT_CMDLINE="${DRONE_BOOT_CMDLINE:-/boot/firmware/cmdline.txt}"

if [ ! -f "$BOOT_CONFIG" ]; then
    log_warn "No $BOOT_CONFIG; skipping UART config (likely non-Pi host)"
    mark_step_done "$STEP"
    exit 0
fi

# Back up once.
[ -f "$BOOT_CONFIG.drone-bak-uart" ]  || cp "$BOOT_CONFIG"  "$BOOT_CONFIG.drone-bak-uart"
[ -f "$BOOT_CMDLINE.drone-bak-uart" ] || cp "$BOOT_CMDLINE" "$BOOT_CMDLINE.drone-bak-uart"

ensure_line() {
    local line="$1" file="$2"
    grep -Fxq "$line" "$file" || printf '%s\n' "$line" >> "$file"
}

# 1. Force enable_uart=1 in config.txt (drop any existing differing value first).
sed -i -E '/^enable_uart=/d' "$BOOT_CONFIG"
ensure_line 'enable_uart=1' "$BOOT_CONFIG"

# 2. Disable Bluetooth so /dev/serial0 → /dev/ttyAMA0 (real PL011).
ensure_line 'dtoverlay=disable-bt' "$BOOT_CONFIG"

# 3. Remove any kernel serial console (frees GPIO UART for our use).
if [ -f "$BOOT_CMDLINE" ]; then
    sed -i -E 's/console=serial[0-9]+,[0-9]+ ?//g; s/console=ttyAMA[0-9]+,[0-9]+ ?//g; s/console=ttyS[0-9]+,[0-9]+ ?//g; s/  +/ /g; s/^ +//; s/ +$//' "$BOOT_CMDLINE"
fi

# 4. Disable any serial getty + hciuart so they don't re-grab the UART after reboot.
SYSTEMCTL="${DRONE_SYSTEMCTL:-systemctl}"
for unit in serial-getty@ttyS0.service serial-getty@ttyAMA0.service serial-getty@serial0.service hciuart.service; do
    if "$SYSTEMCTL" list-unit-files | grep -qE "^${unit}"; then
        "$SYSTEMCTL" disable --now "$unit" 2>/dev/null || true
    fi
done

log_warn "UART configured. REBOOT REQUIRED for /dev/serial0 to come up as real PL011."

mark_step_done "$STEP"
