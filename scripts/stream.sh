#!/bin/bash
# QGroundControl-friendly H.264/RTP stream. Tuned for quality over latency.
# Defaults below can be overridden via /etc/default/drone-video (EnvironmentFile).
set -u

: "${GCS_HOST:=192.168.68.53}"
: "${GCS_PORT:=5600}"
: "${SNAP_PORT:=}"
: "${WIDTH:=640}"
: "${HEIGHT:=480}"
: "${FPS:=20}"
: "${BITRATE:=600000}"
: "${INTRA:=5}"
: "${PROFILE:=baseline}"
: "${LEVEL:=4}"
: "${AF_MODE:=continuous}"
: "${EV:=0}"
: "${FEC_PCT:=0}"

CLIENTS="${GCS_HOST}:${GCS_PORT}"
if [ -n "${SNAP_PORT}" ]; then
    CLIENTS="${CLIENTS},${GCS_HOST}:${SNAP_PORT}"
fi

FEC_STAGE=""
if [ "${FEC_PCT}" -gt 0 ] 2>/dev/null; then
    FEC_STAGE="! rtpulpfecenc pt=122 percentage=${FEC_PCT}"
fi

exec /usr/bin/rpicam-vid \
    --timeout 0 --nopreview --inline --flush \
    --width "$WIDTH" --height "$HEIGHT" --framerate "$FPS" \
    --codec h264 --bitrate "$BITRATE" --intra "$INTRA" \
    --profile "$PROFILE" --level "$LEVEL" \
    --autofocus-mode "$AF_MODE" --ev "$EV" --awb auto \
    --output - \
  | /usr/bin/gst-launch-1.0 --gst-debug-level=1 -e \
      fdsrc fd=0 do-timestamp=true \
      ! video/x-h264,stream-format=byte-stream,alignment=au \
      ! h264parse config-interval=-1 \
      ! rtph264pay pt=96 config-interval=-1 mtu=1200 \
      $FEC_STAGE \
      ! multiudpsink clients="$CLIENTS" sync=false async=false 2>/tmp/gst.err
