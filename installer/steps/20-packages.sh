#!/usr/bin/env bash
# 20-packages.sh — install baseline apt packages + ZeroTier apt source
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="20-packages"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

PACKAGES=(
    python3-venv python3-pip
    git ca-certificates curl gnupg
    gstreamer1.0-tools
    gstreamer1.0-plugins-base
    gstreamer1.0-plugins-good
    gstreamer1.0-plugins-bad
    gstreamer1.0-plugins-ugly
    gstreamer1.0-libav
    meson ninja-build pkg-config build-essential
    nftables
    network-manager
    avahi-daemon
    usb-modeswitch usb-modeswitch-data
    rpicam-apps
)

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y "${PACKAGES[@]}"

if ! command -v zerotier-cli >/dev/null 2>&1; then
    log_info "Adding ZeroTier apt source"
    curl -fsSL 'https://raw.githubusercontent.com/zerotier/ZeroTierOne/master/doc/contact%40zerotier.com.gpg' \
        | gpg --dearmor -o /usr/share/keyrings/zerotier.gpg
    CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"
    echo "deb [signed-by=/usr/share/keyrings/zerotier.gpg] http://download.zerotier.com/debian/${CODENAME} ${CODENAME} main" \
        > /etc/apt/sources.list.d/zerotier.list
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y zerotier-one
else
    log_info "ZeroTier already installed"
fi

mark_step_done "$STEP"
