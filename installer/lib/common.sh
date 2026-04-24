# shellcheck shell=bash
# Shared helpers for installer/steps/*.sh scripts. Source, don't execute.

# Colors only when stdout is a TTY.
if [ -t 1 ]; then
    _DRONE_COLOR_INFO="\033[0;36m"
    _DRONE_COLOR_WARN="\033[0;33m"
    _DRONE_COLOR_ERROR="\033[0;31m"
    _DRONE_COLOR_OK="\033[0;32m"
    _DRONE_COLOR_RESET="\033[0m"
else
    _DRONE_COLOR_INFO=""; _DRONE_COLOR_WARN=""; _DRONE_COLOR_ERROR=""
    _DRONE_COLOR_OK=""; _DRONE_COLOR_RESET=""
fi

log_info()  { printf '%b[INFO]%b  %s\n'  "$_DRONE_COLOR_INFO"  "$_DRONE_COLOR_RESET" "$*"; }
log_warn()  { printf '%b[WARN]%b  %s\n'  "$_DRONE_COLOR_WARN"  "$_DRONE_COLOR_RESET" "$*" >&2; }
log_error() { printf '%b[ERROR]%b %s\n' "$_DRONE_COLOR_ERROR" "$_DRONE_COLOR_RESET" "$*" >&2; }
log_ok()    { printf '%b[OK]%b    %s\n'  "$_DRONE_COLOR_OK"    "$_DRONE_COLOR_RESET" "$*"; }

log_step() {
    local n="$1" m="$2"; shift 2
    printf '%b[%s/%s]%b %s\n' "$_DRONE_COLOR_INFO" "$n" "$m" "$_DRONE_COLOR_RESET" "$*"
}

# Read /proc/device-tree/model. Override DRONE_DT_MODEL_PATH for tests.
detect_pi_model() {
    local path="${DRONE_DT_MODEL_PATH:-/proc/device-tree/model}"
    if [ ! -r "$path" ]; then
        echo "unknown"
        return 1
    fi
    tr -d '\0' < "$path"
}

is_pi_zero2w() { [[ "$(detect_pi_model)" == *"Pi Zero 2"* ]]; }
is_pi4()       { [[ "$(detect_pi_model)" == *"Pi 4"* ]]; }
is_pi5()       { [[ "$(detect_pi_model)" == *"Pi 5"* ]]; }

_drone_marker_dir() { echo "${DRONE_MARKER_DIR:-/var/lib/drone/markers}"; }

mark_step_done() {
    local step="$1"
    local dir; dir=$(_drone_marker_dir)
    mkdir -p "$dir"
    : > "$dir/$step.done"
}

is_step_done() {
    local step="$1"
    local dir; dir=$(_drone_marker_dir)
    [ -f "$dir/$step.done" ]
}

require_root() {
    local euid="${DRONE_FAKE_EUID:-${EUID:-$(id -u)}}"
    if [ "$euid" -ne 0 ]; then
        log_error "This script must be run as root (try: sudo $0)"
        return 1
    fi
    return 0
}
