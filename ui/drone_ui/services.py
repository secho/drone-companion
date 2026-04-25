"""Thin wrappers around host CLIs (systemctl, zerotier-cli, mmcli, etc.).

All external-command calls from the UI go through this module so tests can
patch `_run` without touching the host.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Literal

VALID_SUBSYSTEMS = frozenset({"video", "mavlink", "zerotier", "lte", "all"})

ServiceState = Literal[
    "active", "inactive", "failed", "activating", "deactivating", "unknown"
]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


# ---------- systemd ----------

def systemctl_is_active(service: str) -> ServiceState:
    cp = _run(["systemctl", "is-active", service])
    state = cp.stdout.strip() or "unknown"
    if state not in {"active", "inactive", "failed", "activating", "deactivating", "unknown"}:
        return "unknown"
    return state  # type: ignore[return-value]


def systemctl_restart(service: str) -> subprocess.CompletedProcess:
    return _run(["sudo", "-n", "systemctl", "try-restart", service])


def journalctl_tail(service: str, lines: int = 20) -> str:
    cp = _run(["journalctl", "-u", service, "-n", str(lines), "--no-pager"])
    return cp.stdout


# ---------- ZeroTier ----------

@dataclass(frozen=True)
class ZerotierInfo:
    node_id: str
    version: str
    online: bool


def zerotier_info() -> ZerotierInfo:
    # zerotier-cli reads /var/lib/zerotier-one/authtoken.secret which is root-only,
    # so even read-only commands need sudo here.
    cp = _run(["sudo", "-n", "zerotier-cli", "info"])
    parts = cp.stdout.strip().split()
    # "200 info <node> <ver> ONLINE"
    if len(parts) >= 5 and parts[0] == "200" and parts[1] == "info":
        return ZerotierInfo(node_id=parts[2], version=parts[3], online=parts[4] == "ONLINE")
    return ZerotierInfo(node_id="", version="", online=False)


def zerotier_listnetworks() -> list[dict]:
    """Parse `zerotier-cli listnetworks` into a list of dicts."""
    cp = _run(["sudo", "-n", "zerotier-cli", "listnetworks"])
    networks: list[dict] = []
    for line in cp.stdout.splitlines():
        parts = line.split()
        # "200 listnetworks <nwid> <name> <mac> <status> <type> <dev> <ips>"
        if len(parts) >= 8 and parts[0] == "200" and parts[1] == "listnetworks" and parts[2] != "<nwid>":
            networks.append({
                "id": parts[2],
                "name": parts[3],
                "status": parts[5],
                "dev": parts[7],
                "ips": " ".join(parts[8:]) if len(parts) > 8 else "",
            })
    return networks


def zerotier_join(network_id: str) -> subprocess.CompletedProcess:
    if len(network_id) != 16 or not all(c in "0123456789abcdef" for c in network_id.lower()):
        raise ValueError(f"invalid ZT network id: {network_id!r}")
    return _run(["sudo", "-n", "zerotier-cli", "join", network_id.lower()])


def zerotier_leave(network_id: str) -> subprocess.CompletedProcess:
    return _run(["sudo", "-n", "zerotier-cli", "leave", network_id.lower()])


# ---------- reload-config ----------

def reload_config(subsystem: str) -> subprocess.CompletedProcess:
    if subsystem not in VALID_SUBSYSTEMS:
        raise ValueError(f"unknown subsystem: {subsystem!r}")
    return _run(["sudo", "-n", "/opt/drone/scripts/reload-config", subsystem])


# ---------- HiLink LTE ----------

def _hilink_get(path: str) -> dict:
    import urllib.request
    import xml.etree.ElementTree as ET
    try:
        with urllib.request.urlopen(f"http://192.168.8.1{path}", timeout=3) as req:
            root = ET.fromstring(req.read())
            return {child.tag: (child.text or "") for child in root}
    except Exception as e:
        return {"error": str(e)}


def hilink_status() -> dict:
    return _hilink_get("/api/monitoring/status")


def hilink_signal() -> dict:
    return _hilink_get("/api/device/signal")


def hilink_device_info() -> dict:
    return _hilink_get("/api/device/information")


# ---------- System info ----------

def hostname() -> str:
    return _run(["hostname"]).stdout.strip()


def uptime_seconds() -> int:
    try:
        with open("/proc/uptime") as f:
            return int(float(f.read().split()[0]))
    except Exception:
        return 0


def pi_model() -> str:
    try:
        with open("/proc/device-tree/model") as f:
            return f.read().rstrip("\x00")
    except Exception:
        return "unknown"
