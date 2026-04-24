setup() {
    # shellcheck source=./common.sh
    source "$(dirname "$BATS_TEST_FILENAME")/common.sh"
}

@test "log_info prints with [INFO] prefix" {
    run log_info "hello"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[INFO]"* ]]
    [[ "$output" == *"hello"* ]]
}

@test "log_error prints with [ERROR] prefix" {
    run bash -c 'source '"$BATS_TEST_DIRNAME"'/common.sh; log_error "oops" 2>&1 1>/dev/null'
    [ "$status" -eq 0 ]
    [[ "$output" == *"[ERROR]"* ]]
    [[ "$output" == *"oops"* ]]
}

@test "log_step prints [N/M] prefix" {
    run log_step 20 90 "Installing packages"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[20/90]"* ]]
    [[ "$output" == *"Installing packages"* ]]
}

@test "detect_pi_model returns model name from fixture" {
    local f="$BATS_TEST_TMPDIR/model"
    printf 'Raspberry Pi Zero 2 W Rev 1.0\0' > "$f"
    DRONE_DT_MODEL_PATH="$f" run detect_pi_model
    [ "$status" -eq 0 ]
    [ "$output" = "Raspberry Pi Zero 2 W Rev 1.0" ]
}

@test "is_pi_zero2w true when model contains 'Pi Zero 2'" {
    local f="$BATS_TEST_TMPDIR/model"
    printf 'Raspberry Pi Zero 2 W Rev 1.0\0' > "$f"
    DRONE_DT_MODEL_PATH="$f" run is_pi_zero2w
    [ "$status" -eq 0 ]
}

@test "is_pi_zero2w false on Pi 4" {
    local f="$BATS_TEST_TMPDIR/model"
    printf 'Raspberry Pi 4 Model B Rev 1.5\0' > "$f"
    DRONE_DT_MODEL_PATH="$f" run is_pi_zero2w
    [ "$status" -ne 0 ]
}

@test "is_pi5 true when model starts with 'Raspberry Pi 5'" {
    local f="$BATS_TEST_TMPDIR/model"
    printf 'Raspberry Pi 5 Model B Rev 1.0\0' > "$f"
    DRONE_DT_MODEL_PATH="$f" run is_pi5
    [ "$status" -eq 0 ]
}

@test "mark_step_done and is_step_done round-trip" {
    DRONE_MARKER_DIR="$BATS_TEST_TMPDIR/markers" run bash -c '
        source '"$BATS_TEST_DIRNAME"'/common.sh
        mark_step_done "20-packages" || exit 1
        is_step_done "20-packages" || exit 2
        is_step_done "nothing-here" && exit 3
        exit 0
    '
    [ "$status" -eq 0 ]
}

@test "require_root exits 1 when not root" {
    DRONE_FAKE_EUID=1000 run bash -c 'source '"$BATS_TEST_DIRNAME"'/common.sh; require_root'
    [ "$status" -eq 1 ]
}

@test "require_root succeeds when root" {
    DRONE_FAKE_EUID=0 run bash -c 'source '"$BATS_TEST_DIRNAME"'/common.sh; require_root'
    [ "$status" -eq 0 ]
}
