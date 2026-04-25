"""Pydantic models and I/O for /etc/drone/config.yaml."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


def _config_dir() -> Path:
    return Path(os.environ.get("DRONE_CONFIG_DIR", "/etc/drone"))


class VideoConfig(BaseModel):
    codec: Literal["h264", "mjpeg"] = "h264"
    resolution: Literal["640x480", "1280x720", "1920x1080"] = "640x480"
    fps: int = Field(20, ge=5, le=60)
    bitrate: int = Field(600_000, ge=100_000, le=20_000_000)  # h264 only
    profile: Literal["baseline", "main", "high"] = "baseline"  # h264 only
    level: str = "4"
    intra: int = Field(5, ge=1, le=120)  # h264 only
    fec_percent: int = Field(0, ge=0, le=100)  # h264 only
    mjpeg_quality: int = Field(60, ge=1, le=100)  # mjpeg only — 50-70 sweet spot
    autofocus: Literal["continuous", "manual", "off"] = "continuous"
    exposure_ev: float = Field(-0.5, ge=-3.0, le=3.0)
    gcs_host: str = "0.0.0.0"
    gcs_port: int = Field(5600, ge=1024, le=65535)
    snapshot_port: int | None = None


class MavlinkEndpoint(BaseModel):
    type: Literal["udp-server", "udp-client", "tcp-server"]
    address: str = "0.0.0.0"
    port: int = Field(..., ge=1, le=65535)


class MavlinkConfig(BaseModel):
    uart_alias: Literal["uart0", "uart2", "uart3", "uart4", "uart5"] = "uart0"
    uart_device: str = "/dev/serial0"  # rendered from uart_alias by reload-config
    baud: Literal[9600, 57600, 115200, 230400, 460800, 921600] = 115200
    endpoints: list[MavlinkEndpoint] = Field(
        default_factory=lambda: [
            MavlinkEndpoint(type="udp-server", port=14550),
            MavlinkEndpoint(type="tcp-server", port=5760),
        ]
    )


# UART alias → device path + GPIO pin pair (BCM) + dtoverlay needed
# Reference: https://www.raspberrypi.com/documentation/computers/configuration.html
UART_OPTIONS: dict[str, dict] = {
    "uart0": {
        "device": "/dev/serial0",
        "gpio_tx": 14, "gpio_rx": 15,
        "physical_tx": 8, "physical_rx": 10,
        "overlay": None,  # primary; only needs disable-bt (step 65 handles it)
        "label": "UART0 — GPIO 14/15 (pins 8/10)",
        "supported_models": ["zero2w", "pi4", "pi5"],
    },
    "uart2": {
        "device": "/dev/ttyAMA1",
        "gpio_tx": 0, "gpio_rx": 1,
        "physical_tx": 27, "physical_rx": 28,
        "overlay": "uart2",
        "label": "UART2 — GPIO 0/1 (pins 27/28) — Pi 4/5 only",
        "supported_models": ["pi4", "pi5"],
    },
    "uart3": {
        "device": "/dev/ttyAMA2",
        "gpio_tx": 4, "gpio_rx": 5,
        "physical_tx": 7, "physical_rx": 29,
        "overlay": "uart3",
        "label": "UART3 — GPIO 4/5 (pins 7/29) — Pi 4/5 only",
        "supported_models": ["pi4", "pi5"],
    },
    "uart4": {
        "device": "/dev/ttyAMA3",
        "gpio_tx": 8, "gpio_rx": 9,
        "physical_tx": 24, "physical_rx": 21,
        "overlay": "uart4",
        "label": "UART4 — GPIO 8/9 (pins 24/21) — Pi 4/5 only",
        "supported_models": ["pi4", "pi5"],
    },
    "uart5": {
        "device": "/dev/ttyAMA4",
        "gpio_tx": 12, "gpio_rx": 13,
        "physical_tx": 32, "physical_rx": 33,
        "overlay": "uart5",
        "label": "UART5 — GPIO 12/13 (pins 32/33) — Pi 4/5 only",
        "supported_models": ["pi4", "pi5"],
    },
}


class ZerotierConfig(BaseModel):
    networks: list[str] = Field(default_factory=list)

    @field_validator("networks")
    @classmethod
    def _validate_network_ids(cls, v: list[str]) -> list[str]:
        for nid in v:
            if len(nid) != 16 or not all(c in "0123456789abcdef" for c in nid.lower()):
                raise ValueError(f"invalid ZeroTier network id: {nid!r}")
        return [nid.lower() for nid in v]


class LteConfig(BaseModel):
    enabled: bool = True
    apn: str | None = None
    sim_pin: str | None = None


class Config(BaseModel):
    first_run: bool = True
    hostname: str = "drone"
    video: VideoConfig = Field(default_factory=VideoConfig)
    mavlink: MavlinkConfig = Field(default_factory=MavlinkConfig)
    zerotier: ZerotierConfig = Field(default_factory=ZerotierConfig)
    lte: LteConfig = Field(default_factory=LteConfig)


DEFAULT_CONFIG: dict = Config().model_dump()


def load_config() -> Config:
    path = _config_dir() / "config.yaml"
    if not path.exists():
        return Config()
    with path.open() as f:
        raw = yaml.safe_load(f) or {}
    return Config(**raw)


def save_config(cfg: Config) -> None:
    cfg_dir = _config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    path = cfg_dir / "config.yaml"
    tmp = path.with_suffix(".yaml.tmp")
    with tmp.open("w") as f:
        yaml.safe_dump(cfg.model_dump(mode="json"), f, sort_keys=False)
    tmp.replace(path)
