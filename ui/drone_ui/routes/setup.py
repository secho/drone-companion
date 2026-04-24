from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from drone_ui import services
from drone_ui.config import load_config, save_config
from drone_ui.main import templates

router = APIRouter(prefix="/setup")


@router.get("", response_class=HTMLResponse)
def setup_root():
    return RedirectResponse("/setup/1", status_code=303)


# Step 1: GCS host
@router.get("/1", response_class=HTMLResponse)
def wiz_gcs(request: Request):
    cfg = load_config()
    return templates.TemplateResponse(request, "setup/gcs.html", {"request": request, "cfg": cfg, "flash": None}
    )


@router.post("/1")
def wiz_gcs_post(gcs_host: str = Form(...)):
    cfg = load_config()
    cfg.video.gcs_host = gcs_host
    save_config(cfg)
    return RedirectResponse("/setup/2", status_code=303)


# Step 2: video preset
@router.get("/2", response_class=HTMLResponse)
def wiz_video(request: Request):
    cfg = load_config()
    return templates.TemplateResponse(request, "setup/video.html",
        {"request": request, "cfg": cfg, "presets": ["480p20_600K", "720p30_3M", "1080p30_6M"]},
    )


@router.post("/2")
def wiz_video_post(preset: str = Form(...)):
    presets = {
        "480p20_600K": ("640x480",   20,   600_000),
        "720p30_3M":   ("1280x720",  30, 3_000_000),
        "1080p30_6M":  ("1920x1080", 30, 6_000_000),
    }
    cfg = load_config()
    res, fps, br = presets.get(preset, presets["480p20_600K"])
    cfg.video.resolution = res  # type: ignore[assignment]
    cfg.video.fps = fps
    cfg.video.bitrate = br
    save_config(cfg)
    return RedirectResponse("/setup/3", status_code=303)


# Step 3: optional ZeroTier
@router.get("/3", response_class=HTMLResponse)
def wiz_zt(request: Request):
    cfg = load_config()
    return templates.TemplateResponse(request, "setup/zerotier.html", {"request": request, "cfg": cfg, "flash": None}
    )


@router.post("/3")
def wiz_zt_post(request: Request, network_id: str = Form("")):
    nid = network_id.strip().lower()
    cfg = load_config()
    if nid:
        try:
            services.zerotier_join(nid)
            if nid not in cfg.zerotier.networks:
                cfg.zerotier.networks.append(nid)
                save_config(cfg)
        except ValueError as e:
            return templates.TemplateResponse(request, "setup/zerotier.html",
                {"request": request, "cfg": cfg, "flash": ("err", str(e))},
                status_code=400,
            )
    return RedirectResponse("/setup/4", status_code=303)


# Step 4: summary + finish
@router.get("/4", response_class=HTMLResponse)
def wiz_summary(request: Request):
    cfg = load_config()
    return templates.TemplateResponse(request, "setup/summary.html", {"request": request, "cfg": cfg})


@router.post("/finish")
def wiz_finish():
    cfg = load_config()
    cfg.first_run = False
    save_config(cfg)
    services.reload_config("all")
    return RedirectResponse("/", status_code=303)
