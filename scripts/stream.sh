#!/bin/bash
# H.264 or MJPEG over RTP/UDP, tuned for low-bandwidth wireless links.
# Defaults below are overridden by /etc/default/drone-video (EnvironmentFile).
set -u

: "${CODEC:=h264}"            # h264 | mjpeg
: "${GCS_HOST:=192.168.68.53}"
: "${GCS_PORT:=5600}"
: "${SNAP_PORT:=}"
: "${WIDTH:=640}"
: "${HEIGHT:=480}"
: "${FPS:=20}"
: "${BITRATE:=600000}"        # H.264 only
: "${INTRA:=5}"               # H.264 only — keyframe period in frames
: "${PROFILE:=baseline}"      # H.264 only
: "${LEVEL:=4}"               # H.264 only
: "${MJPEG_QUALITY:=60}"      # MJPEG only (1-100; 50-70 is the practical range)
: "${AF_MODE:=continuous}"
: "${EV:=0}"
: "${FEC_PCT:=0}"             # H.264 only — ULPFEC (QGC ignores)

CLIENTS="${GCS_HOST}:${GCS_PORT}"
if [ -n "${SNAP_PORT}" ]; then
    CLIENTS="${CLIENTS},${GCS_HOST}:${SNAP_PORT}"
fi

case "$CODEC" in
    h264)
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
              ! multiudpsink clients="$CLIENTS" sync=false async=false
        ;;

    mjpeg)
        # rpicam-vid's MJPEG output is per-frame JPEGs concatenated. We re-encode
        # via gst's jpegenc to control quality precisely (q=$MJPEG_QUALITY).
        # Each frame is independent, so packet loss damages at most one frame —
        # better visual behavior under loss than H.264 at the cost of 3-5x bandwidth.
        exec /usr/bin/rpicam-vid \
            --timeout 0 --nopreview --flush \
            --width "$WIDTH" --height "$HEIGHT" --framerate "$FPS" \
            --codec yuv420 \
            --autofocus-mode "$AF_MODE" --ev "$EV" --awb auto \
            --output - \
          | /usr/bin/gst-launch-1.0 --gst-debug-level=1 -e \
              fdsrc fd=0 do-timestamp=true \
              ! "video/x-raw,format=I420,width=${WIDTH},height=${HEIGHT},framerate=${FPS}/1" \
              ! videoconvert \
              ! jpegenc quality="$MJPEG_QUALITY" \
              ! rtpjpegpay pt=26 mtu=1200 \
              ! multiudpsink clients="$CLIENTS" sync=false async=false
        ;;

    *)
        echo "Unknown CODEC=$CODEC. Use 'h264' or 'mjpeg'." >&2
        exit 2
        ;;
esac
