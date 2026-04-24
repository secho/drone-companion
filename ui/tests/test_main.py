from unittest.mock import patch
from fastapi.testclient import TestClient

from drone_ui.main import app


def test_healthz(tmp_config_dir):
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@patch("drone_ui.routes.status.services")
def test_root_redirects_to_setup_when_first_run(mock_services, tmp_config_dir):
    # tmp_config_dir → no config.yaml → load_config() returns defaults with first_run=True
    client = TestClient(app, follow_redirects=False)
    r = client.get("/")
    assert r.status_code == 303
    assert r.headers["location"] == "/setup/1"


@patch("drone_ui.routes.status.services")
def test_root_renders_dashboard_when_not_first_run(mock_services, tmp_config_dir):
    from drone_ui.config import Config, DEFAULT_CONFIG, save_config
    cfg_dict = DEFAULT_CONFIG | {"first_run": False}
    save_config(Config(**cfg_dict))
    mock_services.systemctl_is_active.side_effect = lambda s: "active"
    mock_services.zerotier_info.return_value = type(
        "Z", (), {"node_id": "abc1234567", "online": True, "version": "1.16"}
    )()
    mock_services.hilink_status.return_value = {"ConnectionStatus": "901"}
    mock_services.hostname.return_value = "drone"
    mock_services.pi_model.return_value = "Raspberry Pi Zero 2 W Rev 1.0"
    mock_services.uptime_seconds.return_value = 3600
    mock_services.journalctl_tail.return_value = "log line\n"

    r = TestClient(app, follow_redirects=False).get("/")
    assert r.status_code == 200
    assert "drone-ui" in r.text
    assert "drone-video" in r.text
