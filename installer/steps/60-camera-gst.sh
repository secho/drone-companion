#!/usr/bin/env bash
# 60-camera-gst.sh — apply Pi camera overlay in /boot/firmware/config.txt
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="60-camera-gst"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

BOOT_CONFIG="${DRONE_BOOT_CONFIG:-/boot/firmware/config.txt}"

if [ ! -f "$BOOT_CONFIG" ]; then
    log_warn "No $BOOT_CONFIG; skipping camera overlay (likely non-Pi host)"
    mark_step_done "$STEP"
    exit 0
fi

ensure_line() {
    local line="$1" file="$2"
    grep -Fxq "$line" "$file" || printf '%s\n' "$line" >> "$file"
}

# Default: IMX708 (Camera Module 3 + Pi 5 cam). User can swap to imx519 manually.
ensure_line 'dtoverlay=imx708' "$BOOT_CONFIG"
log_info "Ensured dtoverlay=imx708 in $BOOT_CONFIG"

mark_step_done "$STEP"
