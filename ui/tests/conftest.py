"""Shared pytest fixtures."""
from pathlib import Path

import pytest


@pytest.fixture
def tmp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Empty /etc/drone substitute. Sets DRONE_CONFIG_DIR."""
    d = tmp_path / "etc-drone"
    d.mkdir()
    monkeypatch.setenv("DRONE_CONFIG_DIR", str(d))
    return d
