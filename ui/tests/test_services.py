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


@patch("drone_ui.services._run")
def test_zerotier_info_offline_when_no_output(mock_run):
    mock_run.return_value = MagicMock(stdout="", returncode=1)
    info = services.zerotier_info()
    assert info.node_id == ""
    assert info.online is False


@patch("drone_ui.services._run")
def test_zerotier_join(mock_run):
    mock_run.return_value = MagicMock(stdout="200 join OK", returncode=0)
    services.zerotier_join("4753cf475f1847d2")
    mock_run.assert_called_with(
        ["sudo", "-n", "zerotier-cli", "join", "4753cf475f1847d2"]
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
            "200 listnetworks 4753cf475f1847d2 crazy_christensen d2:19:df:4f:a7:15 OK PRIVATE feth1126 10.147.19.83/24\n"
        ),
        returncode=0,
    )
    nets = services.zerotier_listnetworks()
    assert len(nets) == 1
    assert nets[0]["id"] == "4753cf475f1847d2"
    assert nets[0]["name"] == "crazy_christensen"
    assert nets[0]["status"] == "OK"
