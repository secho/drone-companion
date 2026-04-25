from pathlib import Path

import pytest

from drone_ui.config import Config, DEFAULT_CONFIG, load_config, save_config


def test_default_config_is_valid():
    c = Config(**DEFAULT_CONFIG)
    assert c.video.resolution == "640x480"
    assert c.video.fps == 20
    assert c.mavlink.uart_device == "/dev/serial0"
    assert c.first_run is True


def test_config_rejects_bad_fps():
    bad = DEFAULT_CONFIG | {"video": DEFAULT_CONFIG["video"] | {"fps": 999}}
    with pytest.raises(Exception):
        Config(**bad)


def test_load_and_save_roundtrip(tmp_config_dir: Path):
    save_config(Config(**DEFAULT_CONFIG))
    yaml_file = tmp_config_dir / "config.yaml"
    assert yaml_file.exists()
    loaded = load_config()
    assert loaded.video.fps == 20


def test_load_returns_defaults_when_missing(tmp_config_dir: Path):
    assert not (tmp_config_dir / "config.yaml").exists()
    cfg = load_config()
    assert cfg.first_run is True
    assert not (tmp_config_dir / "config.yaml").exists()


def test_zerotier_network_id_validation():
    with pytest.raises(Exception):
        Config(**(DEFAULT_CONFIG | {"zerotier": {"networks": ["nothex1234567890"]}}))
    with pytest.raises(Exception):
        Config(**(DEFAULT_CONFIG | {"zerotier": {"networks": ["abc"]}}))
    # Mixed-case input must be normalized to lowercase by the validator.
    ok = Config(**(DEFAULT_CONFIG | {"zerotier": {"networks": ["ABCDEF1234567890"]}}))
    assert ok.zerotier.networks == ["abcdef1234567890"]
