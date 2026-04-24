from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from drone_ui import services
from drone_ui.main import templates

router = APIRouter(prefix="/network")


@router.get("/lte", response_class=HTMLResponse)
def lte_get(request: Request) -> HTMLResponse:
    device = services.hilink_device_info()
    status = services.hilink_status()
    signal = services.hilink_signal()
    return templates.TemplateResponse(request, "network/lte.html",
        {"request": request, "device": device, "status": status, "signal": signal},
    )
