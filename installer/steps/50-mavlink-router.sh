#!/usr/bin/env bash
# 50-mavlink-router.sh — build mavlink-router from source if not already installed
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="50-mavlink-router"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

PREFIX="${DRONE_MAVLINK_PREFIX:-/usr/local}"

if [ -x "$PREFIX/bin/mavlink-routerd" ]; then
    log_info "mavlink-routerd already installed at $PREFIX/bin — skipping build"
    mark_step_done "$STEP"
    exit 0
fi

SRC_DIR="${DRONE_MAVLINK_SRC:-/tmp/mavlink-router-src}"
rm -rf "$SRC_DIR"
git clone --recurse-submodules https://github.com/mavlink-router/mavlink-router.git "$SRC_DIR"
cd "$SRC_DIR"
meson setup build --prefix="$PREFIX" --buildtype=release
ninja -C build
ninja -C build install

mark_step_done "$STEP"
