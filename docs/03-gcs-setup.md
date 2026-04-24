# Connecting your Ground Station

Once the Pi is running, the web UI's status page shows the exact connection strings. Below are step-by-step instructions per GCS.

## QGroundControl

### MAVLink link (telemetry + control)

1. **Application Settings** (gear icon, top-right corner)
2. Left sidebar: **Comm Links**
3. Click **Add**
4. Fill in:
   - **Name:** `drone`
   - **Type:** `TCP`
   - **Host:** `drone.local` (or the Pi's IP — look at the Pi's status dashboard)
   - **TCP Port:** `5760`
5. Click **OK** → select `drone` in the list → **Connect**.

A green dot should appear next to the link within 5 seconds, and vehicle data (battery, mode, attitude) will populate the toolbar.

### Video

1. **Application Settings** → left sidebar: **Video** (or **General → Video Settings** on older versions)
2. **Source:** `UDP h.264 Video Stream`
3. **UDP Port:** `5600`
4. Leave **Host** blank (QGC listens, the Pi pushes).
5. **Aspect Ratio:** `1.777` (default 16:9)
6. **Disable When Disarmed:** unchecked (otherwise you see nothing until the FC reports armed)
7. Close settings → switch to **Fly** view.

Video appears in the PiP window (lower-left) within 1–2 seconds of the pipeline connecting. Click the PiP to make it full-screen.

### ⚠ "Source" dropdown only shows "Video Stream Disabled"

You're on an official QGC v5 macOS DMG, which was compiled without GStreamer. Options:

1. **Easiest:** downgrade to QGC v4.4.5 from the [GitHub releases](https://github.com/mavlink/qgroundcontrol/releases/tag/v4.4.5) — older but has video.
2. **Middle:** use `ffplay` in parallel with QGC. Write a `drone.sdp` file:

   ```
   v=0
   o=- 0 0 IN IP4 0.0.0.0
   s=drone
   c=IN IP4 0.0.0.0
   t=0 0
   m=video 5600 RTP/AVP 96
   a=rtpmap:96 H264/90000
   a=fmtp:96 packetization-mode=1
   ```

   Then:
   ```
   brew install ffmpeg
   ffplay -protocol_whitelist file,udp,rtp -fflags nobuffer -i drone.sdp
   ```

3. **Best (more work):** build QGC v5 from source with GStreamer. See the separate `qgc-macos-build` recipe if you want to go this route.

## Mission Planner (Windows)

### MAVLink link

1. Top-right toolbar — click the **dropdown** next to the Connect button.
2. Select **TCP**.
3. In the popup: enter `drone.local` (or the Pi's IP), port `5760`.
4. Click **Connect**.

### Video

Mission Planner's built-in video widget uses GStreamer under the hood. In the Flight Data tab:

1. Right-click on the HUD / video area.
2. **Video → Set GStreamer Source String**:
   ```
   udpsrc port=5600 caps="application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96" ! rtpjitterbuffer latency=50 ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false
   ```
3. Check **Video → Start**.

## MAVProxy (command-line)

```
pip install MAVProxy
mavproxy.py --master=tcp:drone.local:5760
```

Inside MAVProxy:
```
module load map
module load console
```

Or use `--master=udp:drone.local:14550` if you prefer UDP.

## Multiple GCSs at the same time

MAVLink is a one-producer/many-consumer-friendly protocol. Connect multiple clients simultaneously — one via TCP on 5760, others via UDP on 14550. All will receive telemetry and can send commands. First-come, first-served for commands, so coordinate if multiple operators are controlling.

Add more endpoints on the **MAVLink** page of the web UI — for example a second TCP server for a backup laptop or a UDP-client pushing to a telemetry logger.
