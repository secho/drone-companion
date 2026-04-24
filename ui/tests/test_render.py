from drone_ui.config import Config, DEFAULT_CONFIG
from drone_ui.render import render_drone_video_env, render_mavlink_router_conf


def test_render_drone_video_env_defaults():
    cfg = Config(**DEFAULT_CONFIG)
    out = render_drone_video_env(cfg)
    assert "GCS_HOST=0.0.0.0" in out
    assert "WIDTH=640" in out
    assert "HEIGHT=480" in out
    assert "FPS=20" in out
    assert "BITRATE=600000" in out
    assert "PROFILE=baseline" in out
    assert "SNAP_PORT=\n" in out


def test_render_drone_video_env_720p():
    cfg = Config(**DEFAULT_CONFIG)
    cfg.video.resolution = "1280x720"
    cfg.video.fps = 30
    out = render_drone_video_env(cfg)
    assert "WIDTH=1280" in out
    assert "HEIGHT=720" in out
    assert "FPS=30" in out


def test_render_mavlink_router_conf_defaults():
    cfg = Config(**DEFAULT_CONFIG)
    out = render_mavlink_router_conf(cfg)
    assert "[UartEndpoint fc]" in out
    assert "Device = /dev/serial0" in out
    assert "Baud = 115200" in out
    assert "Port = 14550" in out
    assert "Port = 5760" in out


def test_render_mavlink_router_udp_client_mode():
    cfg = Config(**DEFAULT_CONFIG)
    from drone_ui.config import MavlinkEndpoint
    cfg.mavlink.endpoints = [MavlinkEndpoint(type="udp-client", address="10.0.0.5", port=14560)]
    out = render_mavlink_router_conf(cfg)
    assert "Mode = Normal" in out
    assert "Address = 10.0.0.5" in out
    assert "Port = 14560" in out
