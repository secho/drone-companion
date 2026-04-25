from unittest.mock import patch, MagicMock

import pytest

from drone_ui import services


@patch("drone_ui.services._run")
def test_systemctl_is_active(mock_run):
    mock_run.return_value = MagicMock(stdout="active\n", returncode=0)
    assert services.systemctl_is_active("drone-ui") == "active"
    mock_run.assert_called_with(["systemctl", "is-active", "drone-ui"])


@patch("drone_ui.services._run")
def test_systemctl_restart_via_sudo(mock_run):
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    services.systemctl_restart("drone-video")
    mock_run.assert_called_with(["sudo", "-n", "systemctl", "try-restart", "drone-video"])


@patch("drone_ui.services._run")
def test_zerotier_info_online(mock_run):
    mock_run.return_value = MagicMock(
        stdout="200 info abc1234567 1.16.1 ONLINE\n", returncode=0
    )
    info = services.zerotier_info()
    assert info.node_id == "abc1234567"
    assert info.online is True
    # Regression: zerotier-cli reads /var/lib/zerotier-one/authtoken.secret which is root-only,
    # so even reads must go through sudo -n. (Bug landed in v0.1 deploy on drone2.)
    mock_run.assert_called_with(["sudo", "-n", "zerotier-cli", "info"])


@patch("drone_ui.services._run")
def test_zerotier_listnetworks_uses_sudo(mock_run):
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    services.zerotier_listnetworks()
    mock_run.assert_called_with(["sudo", "-n", "zerotier-cli", "listnetworks"])


@patch("drone_ui.services._run")
def test_zerotier_info_offline_when_no_output(mock_run):
    mock_run.return_value = MagicMock(stdout="", returncode=1)
    info = services.zerotier_info()
    assert info.node_id == ""
    assert info.online is False


@patch("drone_ui.services._run")
def test_zerotier_join(mock_run):
    mock_run.return_value = MagicMock(stdout="200 join OK", returncode=0)
    services.zerotier_join("abcdef1234567890")
    mock_run.assert_called_with(
        ["sudo", "-n", "zerotier-cli", "join", "abcdef1234567890"]
    )


def test_zerotier_join_rejects_bad_id():
    with pytest.raises(ValueError):
        services.zerotier_join("not-a-hex")


@patch("drone_ui.services._run")
def test_reload_config_valid(mock_run):
    mock_run.return_value = MagicMock(stdout="", returncode=0)
    services.reload_config("video")
    mock_run.assert_called_with(
        ["sudo", "-n", "/opt/drone/scripts/reload-config", "video"]
    )


def test_reload_config_rejects_bad_subsystem():
    with pytest.raises(ValueError):
        services.reload_config("lolhax")


@patch("drone_ui.services._run")
def test_zerotier_listnetworks_parses_row(mock_run):
    mock_run.return_value = MagicMock(
        stdout=(
            "200 listnetworks <nwid> <name> <mac> <status> <type> <dev> <ZT assigned ips>\n"
            "200 listnetworks abcdef1234567890 my-network d2:19:df:4f:a7:15 OK PRIVATE feth1126 10.147.20.50/24\n"
        ),
        returncode=0,
    )
    nets = services.zerotier_listnetworks()
    assert len(nets) == 1
    assert nets[0]["id"] == "abcdef1234567890"
    assert nets[0]["name"] == "my-network"
    assert nets[0]["status"] == "OK"
