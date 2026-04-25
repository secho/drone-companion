#!/usr/bin/env bash
# install.sh — drone-companion installer.
# Usage: curl -fsSL https://.../install.sh | sudo bash
#    or: git clone ... && cd drone-companion && sudo ./install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO_URL="${DRONE_REPO_URL:-https://github.com/secho/drone-companion.git}"
REPO_BRANCH="${DRONE_REPO_BRANCH:-main}"

# When piped via curl, SCRIPT_DIR points at a temp dir without our files.
# Detect that and self-bootstrap.
if [ ! -f "$SCRIPT_DIR/installer/lib/common.sh" ]; then
    echo "[INFO] Bootstrapping: cloning $REPO_URL into /opt/drone..."
    mkdir -p /opt
    if [ -d /opt/drone/.git ]; then
        cd /opt/drone && git fetch --depth=1 origin "$REPO_BRANCH" \
            && git reset --hard "origin/$REPO_BRANCH"
    else
        git clone --depth=1 --branch "$REPO_BRANCH" "$REPO_URL" /opt/drone
    fi
    exec /opt/drone/install.sh "$@"
fi

# shellcheck source=installer/lib/common.sh
source "$SCRIPT_DIR/installer/lib/common.sh"

require_root

STEPS_DIR="$SCRIPT_DIR/installer/steps"
mapfile -t STEP_FILES < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9]-*.sh' | sort)

TOTAL=${#STEP_FILES[@]}
LOG_FILE="${DRONE_INSTALL_LOG:-/var/log/drone-install.log}"
mkdir -p "$(dirname "$LOG_FILE")"

{
    echo "=== drone-companion install started $(date -Iseconds) ==="
    for i in "${!STEP_FILES[@]}"; do
        idx=$((i + 1))
        step="${STEP_FILES[$i]}"
        name="$(basename "$step" .sh)"
        log_step "$idx" "$TOTAL" "$name"
        if bash "$step"; then
            log_ok "$name"
        else
            log_error "step failed: $name (see $LOG_FILE)"
            exit 1
        fi
    done
    echo "=== drone-companion install finished $(date -Iseconds) ==="
} 2>&1 | tee -a "$LOG_FILE"

HOST="$(hostname).local"
echo
log_ok "Done."
echo
echo "Open http://${HOST}/ in a browser on the same network to configure your drone."
