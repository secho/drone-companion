"""FastAPI app entry point."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from drone_ui.config import load_config

_BASE = Path(__file__).resolve().parent

app = FastAPI(title="drone-companion UI")
templates = Jinja2Templates(directory=str(_BASE / "templates"))
app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.middleware("http")
async def first_run_gate(request: Request, call_next):
    """Redirect '/' to '/setup/1' while the wizard hasn't been completed."""
    if request.url.path == "/" and load_config().first_run:
        return RedirectResponse("/setup/1", status_code=303)
    return await call_next(request)


# Routers (import late so templates/static mounts are first)
from drone_ui.routes import status as _status       # noqa: E402
from drone_ui.routes import video as _video         # noqa: E402
from drone_ui.routes import mavlink as _mavlink     # noqa: E402
from drone_ui.routes import setup as _setup         # noqa: E402
from drone_ui.routes import system as _system       # noqa: E402
from drone_ui.routes.network import zerotier as _zt # noqa: E402
from drone_ui.routes.network import lte as _lte     # noqa: E402

app.include_router(_status.router)
app.include_router(_video.router)
app.include_router(_mavlink.router)
app.include_router(_setup.router)
app.include_router(_system.router)
app.include_router(_zt.router)
app.include_router(_lte.router)
