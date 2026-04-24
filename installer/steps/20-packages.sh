#!/usr/bin/env bash
# 20-packages.sh — install baseline apt packages + ZeroTier apt source
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="20-packages"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

# Sanity-check DNS. If a previous HiLink LTE dongle left its IP as the only nameserver
# and the dongle is no longer reachable, apt will silently fail. Fix before calling apt.
if ! getent hosts deb.debian.org >/dev/null 2>&1; then
    log_warn "DNS resolution broken (likely stale LTE nameserver). Writing fallback /etc/resolv.conf"
    if [ ! -L /etc/resolv.conf ]; then
        cp /etc/resolv.conf /etc/resolv.conf.drone-bak 2>/dev/null || true
        cat > /etc/resolv.conf <<'EOF_RESOLV'
# Written by drone-companion installer. Edit resolvconf/systemd-resolved config as needed.
nameserver 8.8.8.8
nameserver 1.1.1.1
EOF_RESOLV
    fi
    if ! getent hosts deb.debian.org >/dev/null 2>&1; then
        log_error "DNS still not resolving after fallback. Check network + /etc/resolv.conf."
        exit 1
    fi
fi

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
