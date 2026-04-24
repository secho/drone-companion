from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from drone_ui import services
from drone_ui.main import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def status(request: Request) -> HTMLResponse:
    ctx = {
        "request": request,
        "hostname": services.hostname(),
        "model": services.pi_model(),
        "uptime_s": services.uptime_seconds(),
        "services": {
            name: services.systemctl_is_active(name)
            for name in ("drone-ui", "drone-video", "mavlink-router", "zerotier-one")
        },
        "zerotier": services.zerotier_info(),
        "hilink": services.hilink_status(),
        "logs": {
            name: services.journalctl_tail(name, 15)
            for name in ("drone-video", "mavlink-router")
        },
    }
    return templates.TemplateResponse(request, "status.html", ctx)
