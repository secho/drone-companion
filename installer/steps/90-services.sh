#!/usr/bin/env bash
# 90-services.sh — install systemd units, render initial configs, enable services
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="90-services"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

SYSTEMD_DIR="${DRONE_SYSTEMD_DIR:-/etc/systemd/system}"
SYSTEMCTL="${DRONE_SYSTEMCTL:-systemctl}"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Disable any legacy video-stream.service from a previous pre-drone-companion setup
if "$SYSTEMCTL" list-unit-files | grep -q '^video-stream.service'; then
    log_info "Disabling legacy video-stream.service"
    "$SYSTEMCTL" disable --now video-stream.service || true
fi

install -m 0644 "$REPO_ROOT/services/drone-ui.service"       "$SYSTEMD_DIR/drone-ui.service"
install -m 0644 "$REPO_ROOT/services/drone-video.service"    "$SYSTEMD_DIR/drone-video.service"
install -m 0644 "$REPO_ROOT/services/mavlink-router.service" "$SYSTEMD_DIR/mavlink-router.service"

# Initial render of /etc configs from the YAML so services start with valid files
if ! /opt/drone/scripts/reload-config all 2>&1; then
    log_warn "Initial render failed; UI will still start so user can fix config"
fi

"$SYSTEMCTL" daemon-reload
"$SYSTEMCTL" enable --now drone-ui.service
"$SYSTEMCTL" enable drone-video.service mavlink-router.service

# Start video + mavlink only if the config is past first-run (i.e., user has set GCS host)
PYTHON="${DRONE_PYTHON:-/opt/drone/venv/bin/python}"
if "$PYTHON" -c "from drone_ui.config import load_config; import sys; sys.exit(0 if not load_config().first_run else 1)" 2>/dev/null; then
    "$SYSTEMCTL" start drone-video.service mavlink-router.service || \
        log_warn "Some services failed to start; check journalctl for details"
else
    log_info "first_run=true — video + mavlink will start after setup wizard completes"
fi

mark_step_done "$STEP"
