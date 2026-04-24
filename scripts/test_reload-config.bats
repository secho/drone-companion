setup() {
    export DRONE_CONFIG_DIR="$BATS_TEST_TMPDIR/etc-drone"
    export DRONE_RENDER_ROOT="$BATS_TEST_TMPDIR/rendered"
    export DRONE_SYSTEMCTL=/usr/bin/true
    export DRONE_PYTHON="$HOME/Development/UAS/drone-companion/ui/.venv/bin/python"
    mkdir -p "$DRONE_CONFIG_DIR" "$DRONE_RENDER_ROOT"
    cat > "$DRONE_CONFIG_DIR/config.yaml" <<'YAML'
first_run: false
hostname: drone
video:
  resolution: 1280x720
  fps: 30
  bitrate: 1500000
  profile: baseline
  level: "4"
  intra: 10
  fec_percent: 0
  autofocus: continuous
  exposure_ev: 0.0
  gcs_host: 10.0.0.1
  gcs_port: 5600
  snapshot_port: null
mavlink:
  uart_device: /dev/serial0
  baud: 115200
  endpoints:
    - {type: udp-server, address: 0.0.0.0, port: 14550}
zerotier: {networks: []}
lte: {enabled: true, apn: null, sim_pin: null}
YAML
}

@test "reload-config video renders drone-video under render root" {
    run bash "$HOME/Development/UAS/drone-companion/scripts/reload-config" video
    [ "$status" -eq 0 ]
    [ -f "$DRONE_RENDER_ROOT/default/drone-video" ]
    grep -q 'WIDTH=1280' "$DRONE_RENDER_ROOT/default/drone-video"
    grep -q 'GCS_HOST=10.0.0.1' "$DRONE_RENDER_ROOT/default/drone-video"
}

@test "reload-config mavlink renders main.conf" {
    run bash "$HOME/Development/UAS/drone-companion/scripts/reload-config" mavlink
    [ "$status" -eq 0 ]
    [ -f "$DRONE_RENDER_ROOT/mavlink-router/main.conf" ]
    grep -q 'Port = 14550' "$DRONE_RENDER_ROOT/mavlink-router/main.conf"
}

@test "reload-config copies to .last-good on success" {
    run bash "$HOME/Development/UAS/drone-companion/scripts/reload-config" video
    [ "$status" -eq 0 ]
    [ -f "$DRONE_CONFIG_DIR/config.yaml.last-good" ]
}

@test "reload-config all renders both" {
    run bash "$HOME/Development/UAS/drone-companion/scripts/reload-config" all
    [ "$status" -eq 0 ]
    [ -f "$DRONE_RENDER_ROOT/default/drone-video" ]
    [ -f "$DRONE_RENDER_ROOT/mavlink-router/main.conf" ]
}

@test "reload-config unknown subsystem exits 2" {
    run bash "$HOME/Development/UAS/drone-companion/scripts/reload-config" fnord
    [ "$status" -eq 2 ]
}
