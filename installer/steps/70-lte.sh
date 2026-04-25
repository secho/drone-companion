#!/usr/bin/env bash
# 70-lte.sh — on Pi Zero 2W, switch USB to host mode so LTE dongles enumerate.
# Also sets up a NetworkManager profile for usb0 (HiLink modems) on all hardware.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="70-lte"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

STATE="${DRONE_HARDWARE_STATE:-/run/drone-hw.env}"
if [ -f "$STATE" ]; then
    # shellcheck disable=SC1090
    source "$STATE"
fi

BOOT_CONFIG="${DRONE_BOOT_CONFIG:-/boot/firmware/config.txt}"
BOOT_CMDLINE="${DRONE_BOOT_CMDLINE:-/boot/firmware/cmdline.txt}"

if [ "${DRONE_IS_PI_ZERO2W:-0}" = "1" ] && [ -f "$BOOT_CONFIG" ] && [ -f "$BOOT_CMDLINE" ]; then
    log_info "Pi Zero 2W: enabling USB host mode"

    [ -f "$BOOT_CONFIG.drone-bak" ]  || cp "$BOOT_CONFIG"  "$BOOT_CONFIG.drone-bak"
    [ -f "$BOOT_CMDLINE.drone-bak" ] || cp "$BOOT_CMDLINE" "$BOOT_CMDLINE.drone-bak"

    # Remove g_ether gadget module from boot cmdline
    sed -i -E 's/modules-load=dwc2,g_ether/modules-load=dwc2/' "$BOOT_CMDLINE"

    # Ensure dr_mode=host overlay is present in [all] section; remove bare dwc2 overlay
    if ! grep -qE '^dtoverlay=dwc2,dr_mode=host' "$BOOT_CONFIG"; then
        if grep -qE '^\[all\]' "$BOOT_CONFIG"; then
            sed -i '/^\[all\]$/a dtoverlay=dwc2,dr_mode=host' "$BOOT_CONFIG"
        else
            printf '\n[all]\ndtoverlay=dwc2,dr_mode=host\n' >> "$BOOT_CONFIG"
        fi
    fi
    sed -i -E '/^dtoverlay=dwc2$/d' "$BOOT_CONFIG"

    log_warn "USB host mode configured — reboot required for LTE dongles to enumerate"
else
    log_info "Not a Pi Zero 2W (or no boot files) — skipping USB host-mode tweak"
fi

# Remove legacy systemd-networkd gadget config that pins usb0 to 10.55.0.1/24
# (Raspberry Pi OS ships this when USB-gadget is configured; it conflicts with HiLink DHCP.)
NETWORKD_DIR="${DRONE_NETWORKD_DIR:-/etc/systemd/network}"
if [ -f "$NETWORKD_DIR/10-usb0.network" ]; then
    log_info "Removing legacy systemd-networkd gadget config $NETWORKD_DIR/10-usb0.network"
    mv "$NETWORKD_DIR/10-usb0.network" "$NETWORKD_DIR/10-usb0.network.gadget-bak"
fi

# NetworkManager profile for HiLink dongles on usb0 (DHCP, high metric)
NMCLI="${DRONE_NMCLI:-nmcli}"
if command -v "$NMCLI" >/dev/null 2>&1; then
    # Drop any auto-generated NM profile literally named "usb0" (it picks up settings from the
    # dropped systemd-networkd file above and prevents drone-lte from binding).
    "$NMCLI" connection delete usb0 2>/dev/null || true

    if ! "$NMCLI" connection show drone-lte >/dev/null 2>&1; then
        "$NMCLI" connection add type ethernet ifname usb0 con-name drone-lte \
            ipv4.method auto ipv4.route-metric 800 autoconnect yes 2>/dev/null || \
            log_info "usb0 not present yet — NM profile deferred until dongle connected"
    fi
fi

mark_step_done "$STEP"
