#!/usr/bin/env bash
# 40-zerotier.sh — ensure zerotier-one daemon is enabled. Do NOT auto-join networks.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STEP="40-zerotier"
is_step_done "$STEP" && { log_info "$STEP already done, skipping"; exit 0; }

SYSTEMCTL="${DRONE_SYSTEMCTL:-systemctl}"
"$SYSTEMCTL" enable --now zerotier-one.service

mark_step_done "$STEP"
