"""Render Jinja2 templates from the pydantic Config."""
from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from drone_ui.config import Config


def _template_dir() -> Path:
    # Override for tests / for on-Pi install (templates copied to /opt/drone/templates).
    override = os.environ.get("DRONE_TEMPLATES_DIR")
    if override:
        return Path(override)
    # Relative to repo checkout: ui/drone_ui/render.py → ../../installer/templates
    return Path(__file__).resolve().parent.parent.parent / "installer" / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_template_dir())),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_drone_video_env(cfg: Config) -> str:
    t = _env().get_template("drone-video.env.j2")
    return t.render(**cfg.model_dump())


def render_mavlink_router_conf(cfg: Config) -> str:
    t = _env().get_template("mavlink-router.conf.j2")
    return t.render(**cfg.model_dump())
