from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

from drone_ui import services
from drone_ui.config import MavlinkEndpoint, UART_OPTIONS, available_uart_options, load_config, save_config
from drone_ui.main import templates

router = APIRouter()


def _reboot_required() -> bool:
    return Path("/var/lib/drone/reboot-required").exists()


@router.get("/mavlink", response_class=HTMLResponse)
def mavlink_get(request: Request) -> HTMLResponse:
    cfg = load_config()
    return templates.TemplateResponse(request, "mavlink.html",
        {
            "request": request,
            "mavlink": cfg.mavlink,
            "uart_options": available_uart_options(),
            "current_uart": UART_OPTIONS.get(cfg.mavlink.uart_alias, UART_OPTIONS["uart0"]),
            "reboot_required": _reboot_required(),
            "flash": None,
        },
    )


@router.post("/mavlink", response_class=HTMLResponse)
async def mavlink_post(request: Request) -> HTMLResponse:
    form = await request.form()
    count = int(form.get("endpoint_count", "0"))
    endpoints: list[MavlinkEndpoint] = []
    for i in range(count):
        try:
            endpoints.append(MavlinkEndpoint(
                type=form.get(f"endpoint_type_{i}", "udp-server"),  # type: ignore[arg-type]
                address=form.get(f"endpoint_addr_{i}", "0.0.0.0") or "0.0.0.0",
                port=int(form.get(f"endpoint_port_{i}", "14550")),
            ))
        except Exception as e:
            cfg = load_config()
            return templates.TemplateResponse(request, "mavlink.html",
                {"request": request, "mavlink": cfg.mavlink, "flash": ("err", f"row {i}: {e}")},
                status_code=400,
            )

    cfg = load_config()
    requested_alias = str(form.get("uart_alias", "uart0"))
    if requested_alias in UART_OPTIONS:
        cfg.mavlink.uart_alias = requested_alias  # type: ignore[assignment]
        # uart_device gets re-derived by reload-config from the alias lookup.
        cfg.mavlink.uart_device = UART_OPTIONS[requested_alias]["device"]
    cfg.mavlink.baud = int(form.get("baud", "115200"))  # type: ignore[assignment]
    if endpoints:
        cfg.mavlink.endpoints = endpoints
    save_config(cfg)

    cp = services.reload_config("mavlink")
    if cp.returncode != 0:
        flash = ("err", f"reload failed: {cp.stderr.strip() or 'see journalctl -u mavlink-router'}")
    else:
        flash = ("ok", "Saved and restarted mavlink-router.")

    return templates.TemplateResponse(request, "mavlink.html",
        {
            "request": request,
            "mavlink": cfg.mavlink,
            "uart_options": available_uart_options(),
            "current_uart": UART_OPTIONS.get(cfg.mavlink.uart_alias, UART_OPTIONS["uart0"]),
            "reboot_required": _reboot_required(),
            "flash": flash,
        },
    )
