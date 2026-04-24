from __future__ import annotations

import io
import os
import tarfile
import time
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from drone_ui import services
from drone_ui.main import templates

router = APIRouter(prefix="/system")


@router.get("", response_class=HTMLResponse)
def sys_get(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "system.html",
        {"request": request, "flash": None},
    )


@router.post("/reboot", response_class=HTMLResponse)
def sys_reboot(request: Request) -> HTMLResponse:
    cp = services._run(["sudo", "-n", "/sbin/reboot"])
    flash = ("ok", "Reboot initiated.") if cp.returncode == 0 else ("err", cp.stderr.strip() or "reboot failed")
    return templates.TemplateResponse(request, "system.html", {"request": request, "flash": flash})


@router.get("/diagnostics")
def sys_diagnostics() -> Response:
    """Bundle config + journal tails + install log into a tar.gz."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        cfg_dir = Path(os.environ.get("DRONE_CONFIG_DIR", "/etc/drone"))
        cfg_path = cfg_dir / "config.yaml"
        if cfg_path.exists():
            tar.add(str(cfg_path), arcname="config.yaml")

        journals = []
        for unit in ("drone-ui", "drone-video", "mavlink-router", "zerotier-one"):
            cp = services._run(["journalctl", "-u", unit, "--since", "1 hour ago", "--no-pager"])
            journals.append(f"### {unit}\n{cp.stdout}\n")
        data = "\n".join(journals).encode()
        info = tarfile.TarInfo(name="journal.txt")
        info.size = len(data)
        info.mtime = int(time.time())
        tar.addfile(info, io.BytesIO(data))

        log_path = Path("/var/log/drone-install.log")
        if log_path.exists():
            tar.add(str(log_path), arcname="drone-install.log")

    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/gzip",
        headers={"Content-Disposition": "attachment; filename=drone-diagnostics.tar.gz"},
    )
