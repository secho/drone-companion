#!/usr/bin/env bash
# 10-detect-hardware.sh — write hardware facts to $DRONE_HARDWARE_STATE
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

STATE="${DRONE_HARDWARE_STATE:-/run/drone-hw.env}"
mkdir -p "$(dirname "$STATE")"

model="$(detect_pi_model)"
log_info "Model: $model"

is_zero2w=0; is_pi4=0; is_pi5=0
if is_pi_zero2w; then is_zero2w=1; fi
if is_pi4;       then is_pi4=1; fi
if is_pi5;       then is_pi5=1; fi

cat > "$STATE" <<EOF
DRONE_MODEL="$model"
DRONE_IS_PI_ZERO2W=$is_zero2w
DRONE_IS_PI4=$is_pi4
DRONE_IS_PI5=$is_pi5
EOF

mark_step_done "10-detect-hardware"
