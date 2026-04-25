#!/usr/bin/env bash
# gcs-view-mjpeg.sh — Mac/Linux GCS-side viewer for MJPEG-over-RTP from drone-companion.
#
# Run on your ground station, NOT on the Pi.
#
# Usage:
#   ./gcs-view-mjpeg.sh           # listen on port 5600 (default)
#   ./gcs-view-mjpeg.sh 5601      # listen on a different port
#
# Requires:
#   macOS:    brew install gstreamer gst-plugins-base gst-plugins-good gst-libav
#   Debian:   sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-libav
set -euo pipefail
PORT="${1:-5600}"

exec gst-launch-1.0 -q \
    udpsrc port="$PORT" \
        caps="application/x-rtp,media=video,clock-rate=90000,encoding-name=JPEG,payload=26" \
    ! rtpjitterbuffer latency=80 drop-on-latency=true \
    ! rtpjpegdepay \
    ! jpegdec \
    ! videoconvert \
    ! autovideosink sync=false
