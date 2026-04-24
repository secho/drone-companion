from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from drone_ui import services
from drone_ui.config import load_config, save_config
from drone_ui.main import templates

router = APIRouter(prefix="/network")


@router.get("/zerotier", response_class=HTMLResponse)
def zt_get(request: Request) -> HTMLResponse:
    info = services.zerotier_info()
    live = services.zerotier_listnetworks()
    cfg = load_config()
    return templates.TemplateResponse(request, "network/zerotier.html",
        {
            "request": request,
            "info": info,
            "live_networks": live,
            "known_networks": cfg.zerotier.networks,
            "flash": None,
        },
    )


@router.post("/zerotier", response_class=HTMLResponse)
def zt_post(
    request: Request,
    action: str = Form(...),
    network_id: str = Form(""),
) -> HTMLResponse:
    cfg = load_config()
    nid = network_id.lower().strip()
    flash: tuple[str, str] | None = None
    try:
        if action == "join":
            services.zerotier_join(nid)
            if nid not in cfg.zerotier.networks:
                cfg.zerotier.networks.append(nid)
                save_config(cfg)
            flash = ("ok", f"Joined {nid}")
        elif action == "leave":
            services.zerotier_leave(nid)
            cfg.zerotier.networks = [n for n in cfg.zerotier.networks if n != nid]
            save_config(cfg)
            flash = ("ok", f"Left {nid}")
        else:
            flash = ("err", f"unknown action: {action}")
    except ValueError as e:
        flash = ("err", str(e))

    info = services.zerotier_info()
    live = services.zerotier_listnetworks()
    return templates.TemplateResponse(request, "network/zerotier.html",
        {
            "request": request,
            "info": info,
            "live_networks": live,
            "known_networks": cfg.zerotier.networks,
            "flash": flash,
        },
    )
