"""End-to-end route tests with mocked services layer."""
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from drone_ui.main import app
from drone_ui.config import Config, DEFAULT_CONFIG, save_config, load_config


def _post_setup(cfg_dict: dict | None = None):
    save_config(Config(**{**DEFAULT_CONFIG, "first_run": False, **(cfg_dict or {})}))


@patch("drone_ui.routes.video.services")
def test_get_video_renders_current_values(mock_services, tmp_config_dir):
    _post_setup()
    r = TestClient(app).get("/video")
    assert r.status_code == 200
    assert "480p20_600K" in r.text


@patch("drone_ui.routes.video.services")
def test_post_video_preset_updates_config(mock_services, tmp_config_dir):
    _post_setup()
    mock_services.reload_config.return_value = MagicMock(returncode=0, stderr="")
    r = TestClient(app).post(
        "/video",
        data={
            "preset": "720p30_3M",
            "gcs_host": "10.0.0.50",
            "gcs_port": "5600",
            "autofocus": "continuous",
            "exposure_ev": "-0.5",
        },
    )
    assert r.status_code == 200
    cfg = load_config()
    assert cfg.video.resolution == "1280x720"
    assert cfg.video.fps == 30
    assert cfg.video.gcs_host == "10.0.0.50"
    mock_services.reload_config.assert_called_with("video")


@patch("drone_ui.routes.mavlink.services")
def test_get_mavlink_lists_default_endpoints(mock_services, tmp_config_dir):
    _post_setup()
    r = TestClient(app).get("/mavlink")
    assert r.status_code == 200
    assert "udp-server" in r.text
    assert "14550" in r.text


@patch("drone_ui.routes.mavlink.services")
def test_post_mavlink_saves_endpoints(mock_services, tmp_config_dir):
    _post_setup()
    mock_services.reload_config.return_value = MagicMock(returncode=0, stderr="")
    r = TestClient(app).post(
        "/mavlink",
        data={
            "uart_device": "/dev/serial0",
            "baud": "115200",
            "endpoint_count": "2",
            "endpoint_type_0": "udp-server", "endpoint_addr_0": "0.0.0.0", "endpoint_port_0": "14550",
            "endpoint_type_1": "udp-client", "endpoint_addr_1": "10.0.0.5", "endpoint_port_1": "14560",
        },
    )
    assert r.status_code == 200
    cfg = load_config()
    assert len(cfg.mavlink.endpoints) == 2
    assert cfg.mavlink.endpoints[1].address == "10.0.0.5"


@patch("drone_ui.routes.network.zerotier.services")
def test_get_zerotier_shows_node(mock_services, tmp_config_dir):
    _post_setup()
    mock_services.zerotier_info.return_value = type(
        "Z", (), {"node_id": "abc1234567", "online": True, "version": "1.16"}
    )()
    mock_services.zerotier_listnetworks.return_value = []
    r = TestClient(app).get("/network/zerotier")
    assert r.status_code == 200
    assert "abc1234567" in r.text


@patch("drone_ui.routes.network.zerotier.services")
def test_zerotier_join_valid_id(mock_services, tmp_config_dir):
    _post_setup()
    mock_services.zerotier_info.return_value = type(
        "Z", (), {"node_id": "x", "online": True, "version": "1"}
    )()
    mock_services.zerotier_listnetworks.return_value = []
    r = TestClient(app).post(
        "/network/zerotier",
        data={"action": "join", "network_id": "abcdef1234567890"},
    )
    assert r.status_code == 200
    mock_services.zerotier_join.assert_called_with("abcdef1234567890")
    cfg = load_config()
    assert "abcdef1234567890" in cfg.zerotier.networks


@patch("drone_ui.routes.network.zerotier.services")
def test_zerotier_join_bad_id_shows_error(mock_services, tmp_config_dir):
    _post_setup()
    mock_services.zerotier_info.return_value = type(
        "Z", (), {"node_id": "x", "online": True, "version": "1"}
    )()
    mock_services.zerotier_listnetworks.return_value = []
    mock_services.zerotier_join.side_effect = ValueError("invalid ZT network id: 'not-valid'")
    r = TestClient(app).post(
        "/network/zerotier",
        data={"action": "join", "network_id": "not-valid"},
    )
    assert "invalid" in r.text.lower()


@patch("drone_ui.routes.network.lte.services")
def test_lte_page_shows_warn_when_no_modem(mock_services, tmp_config_dir):
    _post_setup()
    mock_services.hilink_device_info.return_value = {"error": "timeout"}
    mock_services.hilink_status.return_value = {"error": "timeout"}
    mock_services.hilink_signal.return_value = {"error": "timeout"}
    r = TestClient(app).get("/network/lte")
    assert r.status_code == 200
    assert "No HiLink modem" in r.text


def test_system_get(tmp_config_dir):
    _post_setup()
    r = TestClient(app).get("/system")
    assert r.status_code == 200
    assert "Reboot" in r.text
    assert "Download diagnostics" in r.text


@patch("drone_ui.routes.system.services._run")
def test_system_reboot(mock_run, tmp_config_dir):
    _post_setup()
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    r = TestClient(app).post("/system/reboot")
    assert r.status_code == 200
    mock_run.assert_called_with(["sudo", "-n", "/sbin/reboot"])


@patch("drone_ui.routes.system.services._run")
def test_system_diagnostics_returns_gzip(mock_run, tmp_config_dir):
    _post_setup()
    mock_run.return_value = MagicMock(returncode=0, stdout="sample log\n", stderr="")
    r = TestClient(app).get("/system/diagnostics")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/gzip"
    # decode the gzipped tar
    import io, tarfile
    tf = tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz")
    names = tf.getnames()
    assert "config.yaml" in names
    assert "journal.txt" in names


def test_setup_redirect_on_first_run(tmp_config_dir):
    # default (no file) = first_run=True
    r = TestClient(app, follow_redirects=False).get("/")
    assert r.status_code == 303
    assert r.headers["location"] == "/setup/1"


def test_setup_wizard_gcs_step(tmp_config_dir):
    r = TestClient(app).get("/setup/1")
    assert r.status_code == 200
    assert "GCS" in r.text


def test_setup_wizard_post_gcs_moves_to_step_2(tmp_config_dir):
    r = TestClient(app, follow_redirects=False).post(
        "/setup/1", data={"gcs_host": "10.0.0.50"}
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/setup/2"
    cfg = load_config()
    assert cfg.video.gcs_host == "10.0.0.50"


@patch("drone_ui.routes.setup.services")
def test_setup_wizard_finish_clears_first_run(mock_services, tmp_config_dir):
    mock_services.reload_config.return_value = MagicMock(returncode=0)
    # Need to have config saved first
    save_config(Config(**DEFAULT_CONFIG))
    r = TestClient(app, follow_redirects=False).post("/setup/finish")
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    cfg = load_config()
    assert cfg.first_run is False
    mock_services.reload_config.assert_called_with("all")
