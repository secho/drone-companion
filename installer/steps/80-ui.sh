#!/usr/bin/env bash
# 80-ui.sh — create venv, pip install the UI, set up sudoers drop-in
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="80-ui"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

OPT="${DRONE_OPT_PREFIX:-/opt/drone}"
SUDOERS_D="${DRONE_SUDOERS_D:-/etc/sudoers.d}"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

log_info "Creating Python venv at $OPT/venv"
# pip install -e writes drone_ui.egg-info into the source dir, so `drone` must own it
chown -R drone:drone "$REPO_ROOT/ui"
sudo -u drone python3 -m venv "$OPT/venv"
sudo -u drone "$OPT/venv/bin/pip" install --quiet --upgrade pip
sudo -u drone "$OPT/venv/bin/pip" install --quiet -e "$REPO_ROOT/ui"

log_info "Installing scripts into $OPT/scripts"
# If REPO_ROOT == OPT (normal curl|bash flow), the files already live where they need to be.
# Just normalize perms/ownership.
if [ "$(readlink -f "$REPO_ROOT/scripts")" != "$(readlink -f "$OPT/scripts")" ]; then
    install -o drone -g drone -m 0755 "$REPO_ROOT/scripts/reload-config" "$OPT/scripts/reload-config"
    install -o drone -g drone -m 0755 "$REPO_ROOT/scripts/stream.sh"     "$OPT/scripts/stream.sh"
else
    chown drone:drone "$OPT/scripts/reload-config" "$OPT/scripts/stream.sh"
    chmod 0755 "$OPT/scripts/reload-config" "$OPT/scripts/stream.sh"
fi
install -o root -g root -m 0755 "$REPO_ROOT/scripts/drone-update" /usr/local/bin/drone-update

install -d -o drone -g drone -m 0755 "$OPT/templates"
if [ "$(readlink -f "$REPO_ROOT/installer/templates")" != "$(readlink -f "$OPT/templates")" ]; then
    cp "$REPO_ROOT"/installer/templates/*.j2 "$OPT/templates/"
fi
chown drone:drone "$OPT/templates"/*.j2 2>/dev/null || true

log_info "Writing sudoers drop-in"
cat > "$SUDOERS_D/drone-ui" <<'EOF'
# Installed by drone-companion. Narrow allowlist.
drone ALL=(root) NOPASSWD: /usr/bin/systemctl try-restart drone-video.service
drone ALL=(root) NOPASSWD: /usr/bin/systemctl try-restart mavlink-router.service
drone ALL=(root) NOPASSWD: /usr/bin/systemctl restart drone-video.service
drone ALL=(root) NOPASSWD: /usr/bin/systemctl restart mavlink-router.service
drone ALL=(root) NOPASSWD: /opt/drone/scripts/reload-config *
drone ALL=(root) NOPASSWD: /usr/sbin/zerotier-cli join *
drone ALL=(root) NOPASSWD: /usr/sbin/zerotier-cli leave *
drone ALL=(root) NOPASSWD: /sbin/reboot
drone ALL=(root) NOPASSWD: /sbin/shutdown -h now
drone ALL=(root) NOPASSWD: /usr/local/bin/drone-update
EOF
chmod 0440 "$SUDOERS_D/drone-ui"
visudo -c -f "$SUDOERS_D/drone-ui"

mark_step_done "$STEP"
