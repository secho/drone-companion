#!/usr/bin/env bash
# uninstall.sh — tear down drone-companion but leave /etc/drone/config.yaml in place
set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Run as root (sudo $0)" >&2
    exit 1
fi

SYSTEMCTL="${DRONE_SYSTEMCTL:-systemctl}"

"$SYSTEMCTL" disable --now drone-ui.service drone-video.service mavlink-router.service 2>/dev/null || true

rm -f /etc/systemd/system/drone-ui.service \
      /etc/systemd/system/drone-video.service \
      /etc/systemd/system/mavlink-router.service
"$SYSTEMCTL" daemon-reload

rm -f /etc/sudoers.d/drone-ui
rm -f /usr/local/bin/drone-update

rm -rf /opt/drone /var/lib/drone

echo "Leaving /etc/drone/ in place (delete manually if desired)."
userdel drone 2>/dev/null || true
