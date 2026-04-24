#!/usr/bin/env bash
# 30-users-dirs.sh — create drone user + /opt/drone, /etc/drone, /var/log/drone
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="30-users-dirs"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

OPT="${DRONE_OPT_PREFIX:-/opt/drone}"
CFG="${DRONE_CONFIG_DIR:-/etc/drone}"
LOGDIR="${DRONE_LOG_DIR:-/var/log/drone}"

if ! getent passwd drone >/dev/null 2>&1; then
    useradd --system --home-dir "$OPT" --shell /usr/sbin/nologin drone
fi
usermod -aG video,dialout drone || true

install -d -o drone -g drone -m 0755 "$OPT" "$OPT/scripts" "$OPT/templates" "$LOGDIR"
install -d -o root  -g root  -m 0755 "$CFG"

if [ ! -f "$CFG/config.yaml" ]; then
    install -o root -g root -m 0644 "$SCRIPT_DIR/../templates/config.example.yaml" "$CFG/config.yaml"
    log_info "Installed default config.yaml at $CFG/config.yaml"
else
    log_info "$CFG/config.yaml exists — leaving untouched"
fi

mark_step_done "$STEP"
