from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from drone_ui import services
from drone_ui.config import load_config, save_config
from drone_ui.main import templates

router = APIRouter()

# form-preset → (resolution, fps, bitrate)
PRESETS: dict[str, tuple[str, int, int]] = {
    "480p20_600K": ("640x480",   20,   600_000),
    "720p30_3M":   ("1280x720",  30, 3_000_000),
    "1080p30_6M":  ("1920x1080", 30, 6_000_000),
}


def _current_preset(resolution: str, fps: int, bitrate: int) -> str:
    for name, (res, f, br) in PRESETS.items():
        if res == resolution and f == fps and br == bitrate:
            return name
    return "custom"


@router.get("/video", response_class=HTMLResponse)
def video_get(request: Request) -> HTMLResponse:
    cfg = load_config()
    return templates.TemplateResponse(request, "video.html",
        {
            "request": request,
            "video": cfg.video,
            "presets": list(PRESETS.keys()),
            "current_preset": _current_preset(cfg.video.resolution, cfg.video.fps, cfg.video.bitrate),
            "flash": None,
        },
    )


@router.post("/video", response_class=HTMLResponse)
def video_post(
    request: Request,
    preset: str = Form(...),
    codec: str = Form("h264"),
    gcs_host: str = Form(...),
    gcs_port: int = Form(...),
    autofocus: str = Form("continuous"),
    exposure_ev: float = Form(-0.5),
    mjpeg_quality: int = Form(60),
) -> HTMLResponse:
    cfg = load_config()
    if preset in PRESETS:
        res, fps, br = PRESETS[preset]
        cfg.video.resolution = res  # type: ignore[assignment]
        cfg.video.fps = fps
        cfg.video.bitrate = br
    cfg.video.codec = codec  # type: ignore[assignment]
    cfg.video.gcs_host = gcs_host
    cfg.video.gcs_port = gcs_port
    cfg.video.autofocus = autofocus  # type: ignore[assignment]
    cfg.video.exposure_ev = exposure_ev
    cfg.video.mjpeg_quality = mjpeg_quality
    save_config(cfg)

    cp = services.reload_config("video")
    if cp.returncode != 0:
        flash = ("err", f"reload failed: {cp.stderr.strip() or 'see journalctl -u drone-video'}")
    else:
        flash = ("ok", "Saved and restarted drone-video.")

    return templates.TemplateResponse(request, "video.html",
        {
            "request": request,
            "video": cfg.video,
            "presets": list(PRESETS.keys()),
            "current_preset": _current_preset(cfg.video.resolution, cfg.video.fps, cfg.video.bitrate),
            "flash": flash,
        },
    )
